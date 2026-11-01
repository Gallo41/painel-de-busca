"""Gera landing pages de demonstração personalizadas por lead.

Layout fixo por nicho (testado) + textos via Gemini opcional (GEMINI_API_KEY),
com fallback determinístico quando a API não está disponível.
"""
import json
import os
import re
import unicodedata
from html import escape
from typing import Any, Dict, List, Optional

import httpx

from app.database import get_lead, upsert_landing_page

GEMINI_MODEL = os.environ.get("GEMINI_LP_MODEL", "gemini-2.5-flash")

BAD_SITE_PAINS = {"SITE_ANTIGO", "SITE_LENTO", "SEM_HTTPS", "SITE_FORA_DO_AR", "SITE_RUIM", "SEM_SITE"}

# Paleta e textos-base por grupo de nicho.
THEMES: Dict[str, Dict[str, Any]] = {
    "saude": {
        "primary": "#0e7490", "accent": "#14b8a6",
        "services": ["Avaliação e diagnóstico", "Tratamentos personalizados", "Atendimento humanizado"],
        "cta": "Agendar consulta",
    },
    "beleza": {
        "primary": "#9d174d", "accent": "#f472b6",
        "services": ["Atendimento com hora marcada", "Profissionais experientes", "Produtos de qualidade"],
        "cta": "Agendar horário",
    },
    "servicos": {
        "primary": "#1e3a8a", "accent": "#f59e0b",
        "services": ["Orçamento sem compromisso", "Equipe qualificada", "Garantia no serviço"],
        "cta": "Pedir orçamento",
    },
    "comercio": {
        "primary": "#166534", "accent": "#84cc16",
        "services": ["Produtos selecionados", "Preço justo", "Atendimento rápido"],
        "cta": "Falar no WhatsApp",
    },
    "generico": {
        "primary": "#1f2937", "accent": "#6366f1",
        "services": ["Atendimento de qualidade", "Compromisso com o cliente", "Resultados reais"],
        "cta": "Falar no WhatsApp",
    },
}

_GROUP_KEYWORDS = {
    "saude": ("odont", "dent", "clinic", "saude", "médic", "medic", "fisio", "psic", "veterin", "nutri", "estetica", "implante"),
    "beleza": ("salao", "salão", "beleza", "barbear", "cabelo", "manicure", "spa", "estudio"),
    "servicos": ("reform", "constru", "eletric", "encan", "pintur", "advoc", "contab", "engenh", "arquitet", "mecan", "limpeza"),
    "comercio": ("loja", "mercad", "padar", "pizz", "restaur", "pet", "floric", "moveis", "roupa"),
}


def make_slug(title: str, lead_id: int) -> str:
    text = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48].strip("-")
    return f"{text or 'cliente'}-{lead_id}"


def is_eligible_for_landing(lead: Dict[str, Any]) -> bool:
    if not lead.get("has_website"):
        return True
    return (lead.get("primary_pain") or "") in BAD_SITE_PAINS


def pick_template(lead: Dict[str, Any]) -> str:
    haystack = f"{lead.get('niche_slug', '')} {lead.get('category', '')}".lower()
    for group, keys in _GROUP_KEYWORDS.items():
        if any(k in haystack for k in keys):
            return group
    return "generico"


def _llm_copy(lead: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    prompt = (
        "Crie textos curtos em português do Brasil para uma landing page de demonstração. "
        f"Empresa: {lead.get('title')}. Segmento: {lead.get('category')}. Cidade: {lead.get('city')}. "
        "Responda APENAS JSON com as chaves: headline (max 70 chars), subheadline (max 140 chars), "
        "services (lista de 3 strings curtas), about (max 280 chars). Não invente prêmios, "
        "preços, endereços nem números."
    )
    try:
        resp = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            headers={"x-goog-api-key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            },
            timeout=20,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
        services = [str(s)[:60] for s in data.get("services", [])][:3]
        if not (data.get("headline") and len(services) == 3):
            return None
        return {
            "headline": str(data["headline"])[:90],
            "subheadline": str(data.get("subheadline", ""))[:180],
            "services": services,
            "about": str(data.get("about", ""))[:320],
        }
    except Exception:
        return None


def build_landing_context(lead: Dict[str, Any], use_llm: bool = True) -> Dict[str, Any]:
    template = pick_template(lead)
    theme = THEMES[template]
    city = lead.get("city") or ""
    category = lead.get("category") or "Atendimento"
    copy = _llm_copy(lead) if use_llm else None
    digits = re.sub(r"\D", "", lead.get("whatsapp_clean") or lead.get("phone") or "")
    if digits and not digits.startswith("55"):
        digits = "55" + digits
    title = lead.get("title") or "Sua empresa"
    wa_text = f"Olá! Vi a página da {title} e gostaria de saber mais."
    from urllib.parse import quote

    return {
        "template": template,
        "title": title,
        "category": category,
        "city": city,
        "address": lead.get("address") or "",
        "phone": lead.get("phone") or "",
        "rating": float(lead.get("review_rating") or 0),
        "review_count": int(lead.get("review_count") or 0),
        "primary": theme["primary"],
        "accent": theme["accent"],
        "cta": theme["cta"],
        "headline": (copy or {}).get("headline") or (f"{category} em {city}" if city else category),
        "subheadline": (copy or {}).get("subheadline")
        or f"{title}: atendimento de confiança, pertinho de você.",
        "services": (copy or {}).get("services") or theme["services"],
        "about": (copy or {}).get("about")
        or f"A {title} atende {city or 'a região'} com dedicação e cuidado em cada cliente.",
        "whatsapp_url": f"https://wa.me/{digits}?text={quote(wa_text)}" if digits else "#contato",
        "content_source": "gemini" if copy else "fallback",
    }


_PAGE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>__TITLE__ | __CATEGORY__</title>
<style>
:root{--p:__PRIMARY__;--a:__ACCENT__}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;color:#1f2937;line-height:1.55}
.demo{background:#111827;color:#fde68a;text-align:center;font-size:.8rem;padding:.4rem}
.hero{background:linear-gradient(135deg,var(--p),var(--a));color:#fff;padding:4.5rem 1.25rem;text-align:center}
.hero h1{font-size:clamp(1.8rem,5vw,3rem);margin:0 0 .75rem}.hero p{max-width:620px;margin:0 auto 1.75rem;opacity:.95}
.btn{display:inline-block;background:#fff;color:var(--p);font-weight:700;padding:.9rem 1.8rem;border-radius:999px;text-decoration:none}
section{max-width:960px;margin:0 auto;padding:3rem 1.25rem}h2{color:var(--p)}
.grid{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.card{border:1px solid #e5e7eb;border-radius:14px;padding:1.25rem;border-top:4px solid var(--a)}
.rating{font-size:1.1rem}footer{background:#f3f4f6;text-align:center;padding:2rem 1rem;font-size:.9rem}
.fab{position:fixed;right:1rem;bottom:1rem;background:#25d366;color:#fff;padding:.9rem 1.2rem;border-radius:999px;text-decoration:none;font-weight:700;box-shadow:0 4px 14px #0004}
</style></head><body>
<div class="demo">Proposta de demonstração, página de exemplo criada para __TITLE__</div>
<header class="hero"><h1>__HEADLINE__</h1><p>__SUBHEADLINE__</p>
<a class="btn" href="__WA__">__CTA__</a></header>
<section><h2>Nossos diferenciais</h2><div class="grid">__SERVICES__</div></section>
<section><h2>Sobre</h2><p>__ABOUT__</p>__RATING__</section>
<section id="contato"><h2>Contato</h2><p>__CONTACT__</p><a class="btn" style="background:var(--p);color:#fff" href="__WA__">__CTA__</a></section>
<footer>__TITLE__ __CITYLINE__</footer>
<a class="fab" href="__WA__">WhatsApp</a>
</body></html>"""


def render_landing_html(ctx: Dict[str, Any]) -> str:
    e = lambda v: escape(str(v), quote=True)  # noqa: E731
    services = "".join(f'<div class="card"><strong>{e(s)}</strong></div>' for s in ctx["services"])
    rating = ""
    if ctx["rating"] > 0:
        rating = f'<p class="rating">★ {ctx["rating"]:.1f}'
        if ctx["review_count"]:
            rating += f' · {ctx["review_count"]} avaliações no Google'
        rating += "</p>"
    contact_bits: List[str] = [b for b in (ctx["address"], ctx["phone"]) if b]
    values = {
        "__TITLE__": e(ctx["title"]), "__CATEGORY__": e(ctx["category"]),
        "__PRIMARY__": e(ctx["primary"]), "__ACCENT__": e(ctx["accent"]),
        "__HEADLINE__": e(ctx["headline"]), "__SUBHEADLINE__": e(ctx["subheadline"]),
        "__CTA__": e(ctx["cta"]), "__WA__": e(ctx["whatsapp_url"]),
        "__SERVICES__": services, "__ABOUT__": e(ctx["about"]), "__RATING__": rating,
        "__CONTACT__": e(" · ".join(contact_bits) or "Fale com a gente pelo WhatsApp."),
        "__CITYLINE__": e(f"· {ctx['city']}") if ctx["city"] else "",
    }
    html = _PAGE
    for key, val in values.items():
        html = html.replace(key, val)
    return html


def generate_landing_for_lead(
    lead_id: int, db_path: Optional[str] = None, use_llm: bool = True
) -> Optional[Dict[str, Any]]:
    lead = get_lead(lead_id, db_path=db_path)
    if not lead:
        return None
    ctx = build_landing_context(lead, use_llm=use_llm)
    html = render_landing_html(ctx)
    return upsert_landing_page(
        lead_id=lead_id,
        slug=make_slug(lead["title"], lead_id),
        template=ctx["template"],
        html=html,
        content_source=ctx["content_source"],
        db_path=db_path,
    )
