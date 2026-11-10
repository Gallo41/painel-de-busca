"""
Ranking de chance de fechamento, segmentação real por nicho e sugestão de preço por lead.

- `detect_segment`: reclassifica o nicho pelo nome/categoria (o `niche_slug` salvo no banco
  nem sempre reflete o negócio real: psicólogas caíram em "academias", construtoras em "imobiliárias").
- `score_close_chance`: nota 0-100 explicável (alcance, dor, capacidade de pagar, decisor, encaixe).
  É um ranking de prioridade, NÃO uma probabilidade calibrada.
- `suggest_price`: preço-alvo/piso/faixa por lead, sempre dentro das faixas oficiais do catálogo do agente.
- `rank_leads`, `group_by_segment`, `build_outreach_plan`: organização para a campanha de disparos.
"""

import csv
import re
import unicodedata
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional, Set

# ---------------------------------------------------------------------------
# Segmentos reais
# ---------------------------------------------------------------------------

# (slug, rótulo, regex, multiplicador de ticket, pontos de encaixe com a oferta "lotar o WhatsApp")
_SEGMENTS = [
    ("construtoras", "Construtoras e Engenharia", r"constru|incorporad|engenharia|empreendimento|loteamento|\bobras?\b", 1.10, 4),
    ("imobiliarias", "Imobiliárias e Corretores", r"imobili|corretor|corretora|\bimoveis\b", 1.05, 5),
    ("advocacia", "Advocacia e Jurídico", r"advoca|advog|juridic|\bdireito\b", 1.08, 6),
    ("odontologia", "Odontologia", r"dent|odonto|ortodon|implante|sorriso", 1.10, 8),
    ("psicologia", "Psicologia e Terapias", r"psic|psi(?=\W|$)|terapeut|psicanal", 0.85, 7),
    ("estetica", "Estética e Dermatologia", r"estetic|harmoniza|dermato|cosmet|beleza|depila|botox", 1.10, 8),
    ("veterinaria", "Veterinária e Pet", r"veterin|\bpet\b|petshop", 1.00, 6),
    ("academias", "Academias e Studios", r"academia|crossfit|fitness|muscula", 0.95, 6),
    ("fisio_pilates", "Fisioterapia e Pilates", r"fisio|pilates|reabilit|quiropra|osteopat", 0.95, 7),
    ("saude", "Clínicas e Saúde Geral", r"medic|clinic|saude|nutri|cardio|oftalm|consultorio", 1.00, 6),
]
_OTHER_SEGMENT = ("outros", "Outros Segmentos", 0.90, 3)
_SEGMENT_META = {s[0]: {"label": s[1], "ticket": s[3], "fit": s[4]} for s in _SEGMENTS}
_SEGMENT_META[_OTHER_SEGMENT[0]] = {"label": _OTHER_SEGMENT[1], "ticket": _OTHER_SEGMENT[2], "fit": _OTHER_SEGMENT[3]}
_SEGMENT_REGEX = [(s[0], re.compile(s[2])) for s in _SEGMENTS]

_HIGH_TICKET_SEGMENTS = {"odontologia", "advocacia", "construtoras", "estetica"}
_COMPLEX_NEED_SEGMENTS = {"odontologia", "veterinaria", "advocacia", "construtoras", "imobiliarias", "saude"}

_INSTITUTION_REGEX = re.compile(
    r"\.gov\.br|\.edu\.br|prefeitura|universidade|faculdade|\bunimep\b|posto de saude|\bupa\b|santa casa|\bubs\b",
    re.IGNORECASE,
)
_PERSONAL_BRAND_REGEX = re.compile(
    r"^(dr|dra|doutor|doutora|psicologo|psicologa|fisioterapeuta|nutricionista|advogado|advogada|dentista)\b",
    re.IGNORECASE,
)
_BIG_ORG_REGEX = re.compile(r"\b(grupo|rede|hospital|franquia|holding)\b", re.IGNORECASE)

SCOPE_SHORT = {
    "LANDING_PAGE": "Landing Page",
    "SITE_INSTITUCIONAL": "Site Completo",
    "SISTEMA_SOB_MEDIDA": "Sistema",
}

_TIER_LABELS = {
    "A": "Disparar primeiro",
    "B": "Segunda leva",
    "C": "Terceira leva",
    "D": "Baixa prioridade",
    "EXCLUIDO": "Não abordar",
}


def _norm(text: Any) -> str:
    raw = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in raw if not unicodedata.combining(c)).lower().strip()


def detect_segment(lead: Dict[str, Any]) -> Dict[str, str]:
    """Segmento real do negócio: nome/categoria primeiro, `niche_slug` só como último recurso."""
    haystack = f"{_norm(lead.get('title'))} {_norm(lead.get('category'))}"
    for slug, rx in _SEGMENT_REGEX:
        if rx.search(haystack):
            return {"slug": slug, "label": _SEGMENT_META[slug]["label"]}
    # 2ª passada: perfil/site (ex.: instagram.com/valfreitaspsi)
    social = f"{_norm(lead.get('instagram'))} {_norm(lead.get('website'))}"
    social = re.sub(r"https?://(www\.)?|[?&].*$", " ", social)
    for slug, rx in _SEGMENT_REGEX:
        if rx.search(social):
            return {"slug": slug, "label": _SEGMENT_META[slug]["label"]}
    slug_text = _norm(lead.get("niche_slug")).replace("-", " ")
    for slug, rx in _SEGMENT_REGEX:
        if rx.search(slug_text):
            # "Dr./Dra." num nicho de academia/pilates é profissional de saúde, não academia
            if slug in ("academias", "fisio_pilates") and re.match(r"^(dr|dra|doutor|doutora)\b", _norm(lead.get("title"))):
                return {"slug": "saude", "label": _SEGMENT_META["saude"]["label"]}
            return {"slug": slug, "label": _SEGMENT_META[slug]["label"]}
    return {"slug": _OTHER_SEGMENT[0], "label": _OTHER_SEGMENT[1]}


# ---------------------------------------------------------------------------
# Canal de contato
# ---------------------------------------------------------------------------


def normalize_phone(lead: Dict[str, Any]) -> str:
    digits = re.sub(r"\D", "", str(lead.get("whatsapp_clean") or lead.get("phone") or ""))
    if len(digits) in (10, 11):
        digits = "55" + digits
    return digits


def contact_channel(lead: Dict[str, Any]) -> str:
    """
    'whatsapp' só para celular (DDD + 9 dígitos). Fixo com `whatsapp_clean` preenchido
    (comum no banco) NÃO conta: a mensagem não chega a ninguém.
    """
    digits = normalize_phone(lead)
    if len(digits) == 13 and digits.startswith("55") and digits[4] == "9":
        return "whatsapp"
    if digits:
        return "telefone"
    if lead.get("instagram"):
        return "instagram"
    if lead.get("emails"):
        return "email"
    return "nenhum"


# ---------------------------------------------------------------------------
# Chance de fechar
# ---------------------------------------------------------------------------

_PAIN_POINTS = {
    "SITE_FORA_DO_AR": (30, "Site fora do ar: perde cliente hoje"),
    "DOMINIO_LIVRE": (28, "Usa só rede social e o domínio está livre"),
    "SEM_SITE": (26, "Sem site próprio"),
    "SITE_AMADOR_ANTIGO": (22, "Site antigo/fraco"),
    "OPORTUNIDADE_SISTEMA": (12, "Já tem site: venda é upgrade/sistema"),
}

_REACH_POINTS = {"whatsapp": 26, "telefone": 6, "instagram": 8, "email": 8, "nenhum": 0}
_REACH_LABEL = {
    "whatsapp": "Celular com WhatsApp direto",
    "telefone": "Só telefone fixo (recepção)",
    "instagram": "Só Instagram (DM)",
    "email": "Só e-mail",
    "nenhum": "Sem canal de contato",
}


def _reviews(lead: Dict[str, Any]) -> int:
    try:
        return int(float(lead.get("review_count") or 0))
    except (TypeError, ValueError):
        return 0


def _tier_for(score: int) -> str:
    if score >= 82:
        return "A"
    if score >= 68:
        return "B"
    if score >= 54:
        return "C"
    return "D"


def is_institution(lead: Dict[str, Any]) -> bool:
    return bool(_INSTITUTION_REGEX.search(f"{_norm(lead.get('title'))} {_norm(lead.get('website'))}"))


def score_close_chance(lead: Dict[str, Any]) -> Dict[str, Any]:
    flags: List[str] = []
    channel = contact_channel(lead)

    if lead.get("lead_status") == "nao_fazer":
        return {"score": 0, "tier": "EXCLUIDO", "tier_label": _TIER_LABELS["EXCLUIDO"], "channel": channel,
                "factors": [], "flags": ["DESCARTADO_MANUALMENTE"]}
    if str(lead.get("place_id") or "").startswith("sim_") or lead.get("source") == "cnae_recem_abertas":
        return {"score": 0, "tier": "EXCLUIDO", "tier_label": _TIER_LABELS["EXCLUIDO"], "channel": channel,
                "factors": [], "flags": ["LEAD_SIMULADO"]}
    if is_institution(lead):
        return {"score": 0, "tier": "EXCLUIDO", "tier_label": _TIER_LABELS["EXCLUIDO"], "channel": channel,
                "factors": [], "flags": ["INSTITUICAO_PUBLICA_OU_ENSINO"]}

    factors: List[Dict[str, Any]] = []

    # 1) Alcance (máx 30)
    reach = _REACH_POINTS[channel]
    factors.append({"label": _REACH_LABEL[channel], "points": reach})
    if channel in ("whatsapp", "telefone") and (lead.get("instagram") or lead.get("emails")):
        factors.append({"label": "Segundo ponto de contato (Instagram/e-mail)", "points": 4})

    # 2) Dor / urgência (máx 30)
    pain_pts, pain_label = _PAIN_POINTS.get(lead.get("primary_pain") or "", (10, "Dor não classificada"))
    if lead.get("primary_pain") == "SEM_SITE" and lead.get("domain_available_br"):
        pain_pts += 2
        pain_label += " (domínio livre)"
    factors.append({"label": pain_label, "points": pain_pts})

    # 3) Capacidade de pagar / prova social (máx 20)
    reviews = _reviews(lead)
    if reviews >= 100:
        cap = 20
    elif reviews >= 40:
        cap = 17
    elif reviews >= 15:
        cap = 12
    elif reviews >= 5:
        cap = 7
    else:
        cap = 3
    factors.append({"label": f"Negócio estabelecido ({reviews} avaliações)", "points": cap})

    # 4) Decisor acessível (máx 12)
    title = _norm(lead.get("title"))
    if _BIG_ORG_REGEX.search(title) or reviews >= 300:
        decisor, dlabel = 2, "Estrutura grande: decisão lenta"
    elif _PERSONAL_BRAND_REGEX.search(title):
        decisor, dlabel = 12, "Profissional autônomo: decide sozinho"
    else:
        decisor, dlabel = 7, "Pequena empresa/clínica"
    factors.append({"label": dlabel, "points": decisor})

    # 5) Encaixe do nicho com a oferta (máx 8)
    seg = detect_segment(lead)
    factors.append({"label": f"Encaixe do nicho ({seg['label']})", "points": _SEGMENT_META[seg["slug"]]["fit"]})

    score = max(0, min(100, sum(f["points"] for f in factors)))
    tier = _tier_for(score)
    if lead.get("lead_status") in ("fazendo", "fechado"):
        flags.append("EM_ANDAMENTO")
    if channel != "whatsapp":
        flags.append("SEM_WHATSAPP_DIRETO")
    return {"score": score, "tier": tier, "tier_label": _TIER_LABELS[tier], "channel": channel,
            "factors": factors, "flags": flags}


# ---------------------------------------------------------------------------
# Preço
# ---------------------------------------------------------------------------


def _catalog() -> Dict[str, Dict[str, Any]]:
    # import tardio: whatsapp_agent também importa este módulo
    from app.services.whatsapp_agent import CATALOGO_SOLUCOES

    return CATALOGO_SOLUCOES


def _band_reais(faixa_preco: str) -> tuple:
    nums = [int(n.replace(".", "")) for n in re.findall(r"R\$\s*([\d.]+)", faixa_preco)]
    return nums[0], nums[1]


def _fmt_reais(reais: int) -> str:
    return "R$ " + f"{int(reais):,}".replace(",", ".")


def _size_factor(reviews: int) -> float:
    if reviews >= 200:
        return 1.12
    if reviews >= 100:
        return 1.06
    if reviews >= 40:
        return 1.00
    if reviews >= 15:
        return 0.93
    if reviews >= 5:
        return 0.87
    return 0.82


def pick_scope(lead: Dict[str, Any]) -> str:
    seg = detect_segment(lead)["slug"]
    reviews = _reviews(lead)
    service = lead.get("recommended_service") or ""
    pain = lead.get("primary_pain") or ""

    if service == "SISTEMA_COMPLEXO" or pain == "OPORTUNIDADE_SISTEMA":
        if reviews >= 40 or (seg in _COMPLEX_NEED_SEGMENTS and reviews >= 15):
            return "SISTEMA_SOB_MEDIDA"
        return "SITE_INSTITUCIONAL"
    if service == "REFORMA_SITE":
        return "SITE_INSTITUCIONAL"
    if reviews >= 60 or (seg in _HIGH_TICKET_SEGMENTS and reviews >= 25):
        return "SITE_INSTITUCIONAL"
    return "LANDING_PAGE"


def suggest_price(lead: Dict[str, Any], scope_type: Optional[str] = None, complex_request: bool = False) -> Dict[str, Any]:
    """Preço-alvo por lead dentro da faixa oficial do escopo (nunca inventa fora do catálogo)."""
    catalog = _catalog()
    scope = scope_type if scope_type in catalog else pick_scope(lead)
    sol = catalog[scope]
    band_min, band_max = _band_reais(sol["faixa_preco"])
    anchor = sol["preco_sugerido_cents"] / 100.0

    seg = detect_segment(lead)
    factor = _SEGMENT_META[seg["slug"]]["ticket"] * _size_factor(_reviews(lead))
    if complex_request:
        factor *= 1.15
    raw = anchor * factor
    alvo = int(round(raw / 50.0) * 50 - 10)
    alvo = max(band_min + 90, min(band_max - 10, alvo))

    piso = max(10, int(round(alvo * 0.75 / 10.0) * 10))
    faixa_min = max(band_min, int(round(alvo * 0.8 / 100.0) * 100))
    faixa_max = min(band_max, int(round(alvo * 1.3 / 100.0) * 100))
    if faixa_max <= alvo:
        faixa_max = band_max
    parcela = int(round(alvo / 3.0))

    return {
        "scope_type": scope,
        "scope_name": sol["nome"],
        "prazo": sol["prazo_medio"],
        "piso_cents": piso * 100,
        "alvo_cents": alvo * 100,
        "faixa_min_cents": faixa_min * 100,
        "faixa_max_cents": faixa_max * 100,
        "faixa_text": f"{_fmt_reais(faixa_min)} a {_fmt_reais(faixa_max)}",
        "alvo_text": _fmt_reais(alvo),
        "piso_text": _fmt_reais(piso),
        "condicao": f"{_fmt_reais(alvo)} à vista ou 3x sem juros (~{_fmt_reais(parcela)}/mês)",
        "justificativa": (
            f"{seg['label']} (ticket x{_SEGMENT_META[seg['slug']]['ticket']:.2f}) e porte de "
            f"{_reviews(lead)} avaliações; escopo {sol['nome']}."
        ),
    }


# ---------------------------------------------------------------------------
# Ranking, grupos e plano de disparo
# ---------------------------------------------------------------------------


def rank_leads(leads: Iterable[Dict[str, Any]], contacted_lead_ids: Optional[Set[int]] = None) -> List[Dict[str, Any]]:
    contacted_lead_ids = contacted_lead_ids or set()
    items: List[Dict[str, Any]] = []
    for lead in leads:
        items.append({
            "lead": lead,
            "segment": detect_segment(lead),
            "close_chance": score_close_chance(lead),
            "price": suggest_price(lead),
        })

    def sort_key(it: Dict[str, Any]):
        lead = it["lead"]
        return (-it["close_chance"]["score"], -_reviews(lead), int(lead.get("id") or 0))

    items.sort(key=sort_key)

    seen_phones: Set[str] = set()
    for it in items:
        cc = it["close_chance"]
        lead = it["lead"]
        phone = normalize_phone(lead)
        if cc["tier"] != "EXCLUIDO" and phone:
            if phone in seen_phones:
                cc["flags"].append("TELEFONE_DUPLICADO")
            seen_phones.add(phone)
        if lead.get("id") in contacted_lead_ids:
            cc["flags"].append("JA_NA_FILA")
        blocking = {"TELEFONE_DUPLICADO", "JA_NA_FILA", "EM_ANDAMENTO", "DESCARTADO_MANUALMENTE", "INSTITUICAO_PUBLICA_OU_ENSINO", "LEAD_SIMULADO"}
        it["outreach_ready"] = (
            cc["channel"] == "whatsapp" and cc["tier"] != "EXCLUIDO" and not (blocking & set(cc["flags"]))
        )

    # excluídos sempre no fim, mantendo a ordem relativa
    items.sort(key=lambda it: it["close_chance"]["tier"] == "EXCLUIDO")
    for pos, it in enumerate(items, start=1):
        it["rank"] = pos
    return items


def group_by_segment(ranked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets: Dict[str, Dict[str, Any]] = {}
    for it in ranked:
        seg = it["segment"]
        b = buckets.setdefault(seg["slug"], {"slug": seg["slug"], "label": seg["label"], "leads": []})
        b["leads"].append(it)

    groups: List[Dict[str, Any]] = []
    for b in buckets.values():
        b["leads"].sort(key=lambda it: (it["close_chance"]["tier"] == "EXCLUIDO", it["rank"]))
        valid = [x for x in b["leads"] if x["close_chance"]["tier"] != "EXCLUIDO"]
        b["total"] = len(b["leads"])
        b["ready"] = sum(1 for x in b["leads"] if x["outreach_ready"])
        b["tier_a"] = sum(1 for x in valid if x["close_chance"]["tier"] == "A")
        b["avg_score"] = round(sum(x["close_chance"]["score"] for x in valid) / len(valid), 1) if valid else 0.0
        groups.append(b)

    groups.sort(key=lambda g: (-g["leads"][0]["close_chance"]["score"], -g["tier_a"], -g["avg_score"]))
    return groups


def build_outreach_plan(
    ranked: List[Dict[str, Any]],
    per_day: int = 20,
    start_date: Optional[date] = None,
    tiers: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    """Fatia os leads prontos (celular, sem duplicata) em dias de disparo, melhores primeiro."""
    allowed = set(tiers) if tiers else None
    ready = [
        it for it in ranked
        if it["outreach_ready"] and (allowed is None or it["close_chance"]["tier"] in allowed)
    ]
    per_day = max(1, per_day)
    plan: List[Dict[str, Any]] = []
    current = start_date
    for i in range(0, len(ready), per_day):
        day_date = None
        if current is not None:
            while current.weekday() >= 5:  # pula sábado/domingo
                current += timedelta(days=1)
            day_date = current.isoformat()
            current += timedelta(days=1)
        plan.append({"day": len(plan) + 1, "date": day_date, "leads": ready[i:i + per_day]})
    return plan


def compact_item(it: Dict[str, Any]) -> Dict[str, Any]:
    """Versão enxuta (JSON-friendly) de um item ranqueado para a API."""
    lead, cc = it["lead"], it["close_chance"]
    return {
        "rank": it["rank"],
        "lead_id": lead.get("id"),
        "title": lead.get("title"),
        "city": lead.get("city"),
        "whatsapp": normalize_phone(lead),
        "segment": it["segment"],
        "primary_pain": lead.get("primary_pain"),
        "review_count": _reviews(lead),
        "tier": cc["tier"],
        "tier_label": cc["tier_label"],
        "score": cc["score"],
        "channel": cc["channel"],
        "flags": cc["flags"],
        "factors": cc["factors"],
        "outreach_ready": it["outreach_ready"],
        "price": it["price"],
    }


# ---------------------------------------------------------------------------
# Exportações
# ---------------------------------------------------------------------------

_CSV_FIELDS = [
    "rank", "tier", "chance", "segmento", "nome", "cidade", "whatsapp", "canal", "dor", "avaliacoes",
    "escopo", "preco_alvo", "preco_piso", "faixa_para_cliente", "pronto_para_disparo", "alertas", "id",
]


def export_ranking_csv(ranked: List[Dict[str, Any]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS, delimiter=";")
        writer.writeheader()
        for it in ranked:
            lead, cc, pr = it["lead"], it["close_chance"], it["price"]
            writer.writerow({
                "rank": it["rank"], "tier": cc["tier"], "chance": cc["score"], "segmento": it["segment"]["label"],
                "nome": lead.get("title"), "cidade": lead.get("city"), "whatsapp": normalize_phone(lead),
                "canal": cc["channel"], "dor": lead.get("primary_pain"), "avaliacoes": _reviews(lead),
                "escopo": pr["scope_name"], "preco_alvo": pr["alvo_text"], "preco_piso": pr["piso_text"],
                "faixa_para_cliente": pr["faixa_text"], "pronto_para_disparo": "sim" if it["outreach_ready"] else "nao",
                "alertas": ",".join(cc["flags"]), "id": lead.get("id"),
            })


def _cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "/").replace("\n", " ")


def render_markdown_report(ranked: List[Dict[str, Any]], groups: List[Dict[str, Any]], plan: List[Dict[str, Any]], top_per_group: int = 10) -> str:
    valid = [r for r in ranked if r["close_chance"]["tier"] != "EXCLUIDO"]
    tiers = {t: sum(1 for r in valid if r["close_chance"]["tier"] == t) for t in "ABCD"}
    ready = sum(1 for r in ranked if r["outreach_ready"])
    out: List[str] = [
        "# Ranking de leads: chance de fechar e preço sugerido",
        "",
        f"- Total: **{len(ranked)}** | prontos para disparo no WhatsApp: **{ready}** | excluídos: **{len(ranked) - len(valid)}**",
        f"- Tiers: A={tiers['A']} · B={tiers['B']} · C={tiers['C']} · D={tiers['D']}",
        "- A nota é prioridade de abordagem (0-100), não probabilidade calibrada. Fixo com `whatsapp_clean` não conta como WhatsApp.",
        "",
        "## Resumo por nicho (melhor oportunidade primeiro)",
        "",
        "| # | Nicho | Leads | Prontos | Tier A | Nota média | Melhor lead |",
        "|:-:|---|:-:|:-:|:-:|:-:|---|",
    ]
    for i, g in enumerate(groups, start=1):
        best = g["leads"][0]
        out.append(f"| {i} | {g['label']} | {g['total']} | {g['ready']} | {g['tier_a']} | {g['avg_score']} | {_cell(best['lead'].get('title'))} ({best['close_chance']['score']}) |")

    for g in groups:
        out += ["", f"## {g['label']} ({g['total']} lead(s))", "",
                "| Rank | Tier | Chance | Lead | WhatsApp | Dor | Oferta | Alvo | Faixa p/ cliente | Obs |",
                "|:-:|:-:|:-:|---|---|---|---|:-:|---|---|"]
        for it in g["leads"][:top_per_group]:
            lead, cc, pr = it["lead"], it["close_chance"], it["price"]
            obs = ",".join(cc["flags"]) or ("ok" if it["outreach_ready"] else "")
            out.append(
                f"| {it['rank']} | {cc['tier']} | {cc['score']} | {_cell(lead.get('title'))} | {normalize_phone(lead)} | "
                f"{lead.get('primary_pain')} | {SCOPE_SHORT.get(pr['scope_type'], pr['scope_type'])} | "
                f"{pr['alvo_text']} | {pr['faixa_text']} | {obs} |"
            )
        if g["total"] > top_per_group:
            out.append(f"\n_+{g['total'] - top_per_group} leads no CSV._")

    out += ["", "## Plano de disparo", ""]
    if not plan:
        out.append("Nenhum lead pronto.")
    for d in plan:
        counts = {t: sum(1 for x in d["leads"] if x["close_chance"]["tier"] == t) for t in "ABCD"}
        when = f" ({d['date']})" if d["date"] else ""
        out.append(f"- **Dia {d['day']}{when}**: {len(d['leads'])} leads (A={counts['A']}, B={counts['B']}, C={counts['C']}, D={counts['D']}), ranks {d['leads'][0]['rank']} a {d['leads'][-1]['rank']}")
    return "\n".join(out) + "\n"
