import csv
import io
import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional

from app.services.niches_catalog import get_niches_by_slugs
import scripts.scrape as kit_scraper


def normalize_whatsapp_br(phone: str) -> str:
    """Converte telefone brasileiro em formato limpo 55DDDNUMERO para links wa.me."""
    if not phone:
        return ""
    digits = re.sub(r"\D+", "", str(phone))
    if not digits:
        return ""
    if digits.startswith("0") and len(digits) in (11, 12):
        digits = digits[1:]
    if digits.startswith("55") and len(digits) in (12, 13):
        return digits
    if len(digits) in (10, 11):
        return "55" + digits
    return ""


def check_scraper_engine_health(timeout: float = 0.8) -> Dict[str, Any]:
    """Verifica rapidamente se o motor Docker gosom/google-maps-scraper está ativo em 127.0.0.1:8080."""
    import urllib.request
    base = kit_scraper.BASE.replace("localhost", "127.0.0.1")
    try:
        req = urllib.request.Request(f"{base}/api/v1/jobs", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
        return {
            "online": status == 200,
            "base_url": kit_scraper.BASE,
            "message": "Motor Google Maps Scraper (Docker) online e pronto.",
        }
    except Exception as exc:
        return {
            "online": False,
            "base_url": kit_scraper.BASE,
            "message": f"Motor Docker offline em {kit_scraper.BASE}. Use 'docker compose up -d' ou o modo Demonstração/Importação CSV.",
            "error": str(exc),
        }


def start_scraper_engine_docker() -> Dict[str, Any]:
    """Tenta iniciar o container Docker do google-maps-scraper-kit."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        proc = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=45,
        )
        health = check_scraper_engine_health()
        return {
            "started": proc.returncode == 0,
            "online": health["online"],
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except Exception as exc:
        return {"started": False, "online": False, "error": str(exc)}


def build_keywords_for_job(
    city: str,
    state: str,
    niche_slugs: List[str],
    custom_keywords: Optional[List[str]] = None,
) -> List[str]:
    place = f"{city.strip()} {state.strip()}".strip()
    niches = get_niches_by_slugs(niche_slugs)
    keywords: List[str] = []
    for n in niches:
        # Pega os 2 principais termos de cada nicho selecionado para evitar excesso de queries
        for term in n.get("search_terms", [])[:2]:
            kw = f"{term} em {place}"
            if kw not in keywords:
                keywords.append(kw)

    for custom in custom_keywords or []:
        c = custom.strip()
        if not c:
            continue
        kw = c if place.lower() in c.lower() else f"{c} em {place}"
        if kw not in keywords:
            keywords.append(kw)

    return keywords


def parse_csv_content_to_leads(
    csv_text: str,
    city: str = "",
    state: str = "SP",
    niche_slug: str = "geral",
    job_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    leads: List[Dict[str, Any]] = []
    for r in reader:
        title = (r.get("title") or r.get("name") or "").strip()
        if not title:
            continue
        phone = (r.get("phone") or "").strip()
        leads.append(
            {
                "job_id": job_id,
                "place_id": (r.get("place_id") or r.get("cid") or "").strip(),
                "niche_slug": niche_slug,
                "title": title,
                "category": (r.get("category") or "").strip(),
                "phone": phone,
                "whatsapp_clean": normalize_whatsapp_br(phone),
                "emails": (r.get("emails") or r.get("email") or "").strip(),
                "website": (r.get("website") or "").strip(),
                "address": (r.get("address") or "").strip(),
                "city": city or (r.get("city") or "").strip(),
                "state": state,
                "review_rating": float(r.get("review_rating") or 0.0),
                "review_count": int(float(r.get("review_count") or 0)),
                "instagram": (r.get("instagram") or "").strip(),
                "facebook": (r.get("facebook") or "").strip(),
                "linkedin": (r.get("linkedin") or "").strip(),
                "cnpj": (r.get("cnpj") or "").strip(),
                "opened_date": (r.get("opened_date") or "").strip(),
                "source": "google_maps",
            }
        )
    return leads


def run_live_maps_scrape(
    city: str,
    state: str,
    niche_slugs: List[str],
    custom_keywords: Optional[List[str]] = None,
    depth: int = 5,
    grid_size: int = 1,
    include_socials: bool = True,
    job_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Executa a busca real usando as funcoes nativas do scripts/scrape.py da skill google-maps-scraper."""
    keywords = build_keywords_for_job(city, state, niche_slugs, custom_keywords)
    place_query = f"{city}, {state}, Brasil"

    if grid_size and grid_size > 1:
        geo = kit_scraper.geocode(place_query, with_bbox=True)
        if not geo or not geo[2]:
            raise RuntimeError(f"Não foi possível geocodificar a área de {place_query}")
        lat, lon, bbox = geo
        cells = kit_scraper.grid_cells(bbox, min(grid_size, 5))
    else:
        coords = kit_scraper.geocode(place_query)
        if not coords:
            raise RuntimeError(f"Não foi possível geocodificar {place_query}")
        lat, lon = coords
        bbox, cells = None, []

    body = {
        "name": f"painel-{city.lower()}",
        "keywords": keywords,
        "lang": "pt",
        "zoom": 15,
        "lat": str(lat),
        "lon": str(lon),
        "fast_mode": False,
        "radius": 10000,
        "depth": depth,
        "email": True,
        "max_time": 600,
    }

    if not cells:
        _, rows = kit_scraper.run_job(body)
    else:
        rows = []
        for cell in cells:
            try:
                _, cell_rows = kit_scraper.run_job(dict(body, **cell))
                rows = kit_scraper.dedupe(rows + cell_rows)
            except Exception:
                continue
        if bbox:
            rows = [r for r in rows if kit_scraper.in_bbox(r, bbox)]

    # Enriquecimento de e-mails e redes sociais nativo da skill (0 tokens de IA)
    kit_scraper.enrich_emails(rows)
    if include_socials:
        kit_scraper.enrich_socials(rows)

    default_niche = niche_slugs[0] if niche_slugs else "geral"
    leads: List[Dict[str, Any]] = []
    for r in rows:
        phone = (r.get("phone") or "").strip()
        leads.append(
            {
                "job_id": job_id,
                "place_id": (r.get("place_id") or r.get("cid") or "").strip(),
                "niche_slug": default_niche,
                "title": (r.get("title") or "").strip(),
                "category": (r.get("category") or "").strip(),
                "phone": phone,
                "whatsapp_clean": normalize_whatsapp_br(phone),
                "emails": (r.get("emails") or "").strip(),
                "website": (r.get("website") or "").strip(),
                "address": (r.get("address") or "").strip(),
                "city": city,
                "state": state,
                "review_rating": float(r.get("review_rating") or 0.0),
                "review_count": int(float(r.get("review_count") or 0)),
                "instagram": (r.get("instagram") or "").strip(),
                "facebook": (r.get("facebook") or "").strip(),
                "linkedin": (r.get("linkedin") or "").strip(),
                "source": "google_maps",
            }
        )
    return leads


def generate_sample_leads_for_niches(
    city: str,
    state: str = "SP",
    niche_slugs: Optional[List[str]] = None,
    job_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Gera leads realistas baseados nos nichos selecionados para validação imediata quando o Docker estiver desligado."""
    selected = get_niches_by_slugs(niche_slugs or ["clinicas-odontologicas", "escritorios-advocacia", "imobiliarias-corretores"])
    city_clean = city.strip() or "Campinas"
    state_clean = state.strip().upper() or "SP"

    templates = [
        # Cenário 1: Sem site nenhum + muitas avaliações + domínio livre (Oportunidade máxima de Site Novo)
        {
            "suffix": f"Prime {city_clean}",
            "phone": "(19) 99812-3401",
            "emails": "",
            "website": "",
            "rating": 4.9,
            "reviews": 87,
            "instagram": "https://instagram.com/prime_atendimento",
            "source": "google_maps",
            "opened_date": "2024-03-15",
            "cnpj": "48.192.301/0001-10",
        },
        # Cenário 2: Usa apenas Linktree ou Instagram como "site" no Google Maps
        {
            "suffix": f"conceito & Cia {city_clean}",
            "phone": "(19) 99745-8821",
            "emails": "contato@conceitoecia.com",
            "website": "https://linktr.ee/conceitoecia",
            "rating": 4.8,
            "reviews": 64,
            "instagram": "https://instagram.com/conceitoecia",
            "source": "google_maps",
            "opened_date": "2025-01-20",
            "cnpj": "51.400.219/0001-88",
        },
        # Cenário 3: Tem site cadastrado no Maps, mas está FORA DO AR (DownForEveryoneOrJustMe)
        {
            "suffix": f"Central {city_clean}",
            "phone": "(19) 99611-0092",
            "emails": "atendimento@centralnegocios-offline.com.br",
            "website": "http://www.centralnegocios-offline-inexistente-999.com.br",
            "rating": 4.6,
            "reviews": 53,
            "instagram": "https://instagram.com/centralnegocios",
            "source": "google_maps",
            "opened_date": "2019-08-10",
            "cnpj": "31.882.104/0001-42",
        },
        # Cenário 4: Empresa consolidada (>140 avaliações), site Wix/antigo sem sistema -> Oportunidade de Sistema Complexo / Reforma
        {
            "suffix": f"Master Group {city_clean}",
            "phone": "(19) 99123-4500",
            "emails": "diretoria@mastergroup.com.br",
            "website": "http://mastergroup-wix-demo.com.br",
            "rating": 4.9,
            "reviews": 165,
            "instagram": "https://instagram.com/mastergroupoficial",
            "source": "google_maps",
            "opened_date": "2017-05-12",
            "cnpj": "24.501.992/0001-05",
        },
        # Cenário 5: Empresa recém-aberta (Casa dos Dados / CNPJ recente) ainda sem presença web
        {
            "suffix": f"Nova Geração {city_clean} LTDA",
            "phone": "(19) 99440-1122",
            "emails": "socios@novageracao.com.br",
            "website": "",
            "rating": 5.0,
            "reviews": 6,
            "instagram": "",
            "source": "casadosdados",
            "opened_date": "2026-09-18",
            "cnpj": "58.910.442/0001-77",
        },
    ]

    leads: List[Dict[str, Any]] = []
    idx = 1
    for niche in selected:
        base_term = (niche.get("search_terms") or [niche["name"]])[0].title()
        for t in templates[:3] if len(selected) > 2 else templates:
            title = f"{base_term} {t['suffix']}"
            leads.append(
                {
                    "job_id": job_id,
                    "place_id": f"sim_{niche['slug']}_{city_clean.lower()}_{idx}",
                    "niche_slug": niche["slug"],
                    "title": title,
                    "category": base_term,
                    "phone": t["phone"],
                    "whatsapp_clean": normalize_whatsapp_br(t["phone"]),
                    "emails": t["emails"],
                    "website": t["website"],
                    "address": f"Av. Principal, {100 + idx * 15} - Centro, {city_clean} - {state_clean}",
                    "city": city_clean,
                    "state": state_clean,
                    "review_rating": t["rating"],
                    "review_count": t["reviews"],
                    "instagram": t["instagram"],
                    "facebook": "",
                    "linkedin": "",
                    "cnpj": t["cnpj"],
                    "opened_date": t["opened_date"],
                    "source": t["source"],
                }
            )
            idx += 1
    return leads
