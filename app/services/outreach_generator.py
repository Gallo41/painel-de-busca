import urllib.parse
from typing import Any, Dict, List, Optional

from app.database import get_lead, update_lead_xray_and_score, upsert_lead
from app.services.lead_scorer import score_and_classify_lead
from app.services.maps_scraper import normalize_whatsapp_br
from app.services.site_xray import run_full_xray_for_lead


def build_ready_report_for_lead(
    lead: Dict[str, Any],
    xray_data: Dict[str, Any],
    score_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Traduz todos os dados técnicos das 8 ferramentas em um Relatório Comercial Pronto,
    intuitivo e mastigado para o usuário bater o olho, saber o que vender e abordar em 1 clique.
    """
    title = (lead.get("title") or "Empresa").strip()
    city = (lead.get("city") or "sua cidade").strip()
    state = (lead.get("state") or "SP").strip()
    reviews = int(float(lead.get("review_count") or 0))
    rating = float(lead.get("review_rating") or 0.0)
    cnpj = (lead.get("cnpj") or "").strip()
    opened = (lead.get("opened_date") or "").strip()

    pain = score_data.get("primary_pain") or "SEM_SITE"
    service = score_data.get("recommended_service") or "SITE_NOVO"
    dom = xray_data.get("suggested_domain") or "empresa.com.br"
    dom_free = bool(xray_data.get("domain_available_br"))
    has_site = bool(xray_data.get("has_website"))
    is_social = bool(xray_data.get("is_social_only_url"))
    in_air = bool(xray_data.get("site_in_air"))
    has_ssl = bool(xray_data.get("has_ssl"))
    cms = xray_data.get("detected_cms") or "Sem Site"
    wb_last = xray_data.get("wayback_last_seen")
    wb_days = xray_data.get("wayback_days_since_update")

    reports = (xray_data.get("external_tools_links") or {}).get("embedded_reports") or {}
    whatcms_rep = reports.get("whatcms") or {}
    reg_rep = reports.get("registro_br") or {}
    missing_opps = whatcms_rep.get("missing_systems_opportunities") or []
    variations = [v.get("domain") for v in (reg_rep.get("variations") or []) if isinstance(v, dict) and v.get("domain")]

    # O que vender + Ticket sugerido
    if service == "SISTEMA_COMPLEXO" or pain == "OPORTUNIDADE_SISTEMA":
        what_to_sell = "Sistema Web Sob Medida (Agendamento / Portal / Catálogo) + Reforma"
        ticket_range = "R$ 3.500 a R$ 8.000"
        category_tab = "sistema"
    elif pain == "SITE_FORA_DO_AR" or service == "REFORMA_SITE":
        what_to_sell = "Reforma Urgente de Site + Hospedagem Segura (HTTPS)"
        ticket_range = "R$ 1.800 a R$ 3.500"
        category_tab = "reforma"
    else:
        what_to_sell = "Criação de Site Profissional / Landing Page + Domínio .com.br"
        ticket_range = "R$ 1.200 a R$ 2.500"
        category_tab = "site_novo"

    if lead.get("source") in ("casadosdados", "cnae_recem_abertas", "receita_cnpj_embutido"):
        category_tab = "recem_aberta"

    # Manchete clara
    if pain == "SITE_FORA_DO_AR":
        headline = f"URGENTE: O site cadastrado no Google Maps está FORA DO AR (perdendo clientes todos os dias)."
    elif not has_site:
        headline = f"NÃO TEM SITE PRÓPRIO no Google Maps ({reviews} avaliações) e o domínio {dom} está {'LIVRE' if dom_free else 'disponível em variação'}."
    elif is_social:
        headline = f"Usa apenas Link na Bio / Rede Social como site ({reviews} avaliações) — oportunidade pronta de Site Profissional."
    elif pain == "OPORTUNIDADE_SISTEMA":
        headline = f"Empresa consolidada ({reviews} avaliações, nota {rating:.1f}) com site {cms} básico sem sistema de agendamento/portal."
    else:
        headline = score_data.get("pain_summary") or "Oportunidade qualificada de modernização digital."

    # 4 Tópicos prontos traduzindo as 8 ferramentas
    bullet_maps_cnpj = (
        f"Nota {rating:.1f} ⭐ ({reviews} avaliações) em {city}-{state}"
        + (f" • CNPJ {cnpj}" if cnpj else "")
        + (f" • Aberta em {opened}" if opened else "")
    )

    if dom_free:
        bullet_domain = f"Domínio {dom} consta como LIVRE no Registro.br (consulta RDAP oficial)."
    else:
        bullet_domain = f"Domínio {dom} já está registrado no Registro.br."

    if not has_site:
        bullet_health = "Empresa não possui nenhum site cadastrado (100% invisível nas buscas orgânicas do Google)."
    elif is_social:
        bullet_health = f"Não tem site próprio: o link do Maps joga apenas para {cms} ({lead.get('website')})."
    elif not in_air:
        bullet_health = f"Site FORA DO AR ({lead.get('website')}) — erro confirmado de servidor/DNS."
    else:
        ssl_txt = "com HTTPS seguro" if has_ssl else "SEM cadeado HTTPS (aviso de 'Site Não Seguro' no navegador)"
        wb_txt = f" • Sem atualização no Web Archive há {wb_days} dias (desde {wb_last})" if wb_days else ""
        bullet_health = f"Site online ({ssl_txt}){wb_txt}."

    if not has_site or is_social:
        bullet_tech = "Precisa de estrutura completa: Página de Alta Conversão + Botão WhatsApp + Pixel de Anúncios."
    else:
        missing_txt = ", ".join(missing_opps[:2]) if missing_opps else "Modernização de layout mobile e conversão"
        bullet_tech = f"Tecnologia atual: {cms} • O que falta implementar: {missing_txt}."

    opp_score = int(score_data.get("opportunity_score") or lead.get("opportunity_score") or 80)
    urgency_badge = "🔥 Prioridade Máxima" if opp_score >= 85 else ("⚡ Alta Chance" if opp_score >= 70 else "📌 Oportunidade")

    return {
        "headline": headline,
        "executive_pitch": headline,
        "urgency_badge": urgency_badge,
        "what_to_sell": what_to_sell,
        "ticket_range": ticket_range,
        "category_tab": category_tab,
        "bullets": [
            {
                "icon": "📍",
                "label": "Presença no Google Maps & CNPJ",
                "status": "ok",
                "text": bullet_maps_cnpj,
            },
            {
                "icon": "🌐",
                "label": "Domínio Oficial (Registro.br)",
                "status": "opportunity" if dom_free else "neutral",
                "text": bullet_domain,
            },
            {
                "icon": "🩺",
                "label": "Saúde do Site & Histórico Web Archive",
                "status": "urgent" if (not has_site or not in_air) else ("warning" if not has_ssl else "ok"),
                "text": bullet_health,
            },
            {
                "icon": "⚙️",
                "label": "Tecnologia & Sistemas Faltantes",
                "status": "opportunity",
                "text": bullet_tech,
            },
        ],
        "missing_opportunities": missing_opps[:4],
    }


def build_executive_summary_report(leads: List[Dict[str, Any]], city: str = "") -> Dict[str, Any]:
    """Consolida os números do Relatório Executivo Pronto para exibição imediata no topo da página."""
    total = len(leads)
    city_label = (city or (leads[0].get("city") if leads else "Sua Região")).strip() or "Sua Região"
    need_new_site = sum(1 for l in leads if (not l.get("has_website")) or l.get("is_social_only_url"))
    site_down_or_broken = sum(
        1 for l in leads if l.get("primary_pain") in ("SITE_FORA_DO_AR", "SITE_AMADOR_ANTIGO")
    )
    need_complex_system = sum(
        1 for l in leads if l.get("recommended_service") == "SISTEMA_COMPLEXO" or l.get("primary_pain") == "OPORTUNIDADE_SISTEMA"
    )
    free_domains = sum(1 for l in leads if l.get("domain_available_br"))
    newly_opened = sum(
        1 for l in leads if l.get("source") in ("casadosdados", "cnae_recem_abertas", "receita_cnpj_embutido") or str(l.get("opened_date") or "").startswith(("2025", "2026"))
    )

    estimated_pipeline_min = (need_new_site * 1200) + (site_down_or_broken * 1800) + (need_complex_system * 3500)
    estimated_pipeline_max = (need_new_site * 2500) + (site_down_or_broken * 3500) + (need_complex_system * 8000)
    if estimated_pipeline_min == 0 and total > 0:
        estimated_pipeline_min = total * 1500
        estimated_pipeline_max = total * 3000

    min_fmt = f"{estimated_pipeline_min:,.0f}".replace(",", ".")
    max_fmt = f"{estimated_pipeline_max:,.0f}".replace(",", ".")

    return {
        "city": city_label,
        "headline": f"Relatório Pronto: {total} Clientes Qualificados em {city_label}",
        "subheadline": (
            f"Encontramos {need_new_site} empresas sem site próprio, {site_down_or_broken} precisando de reforma urgente "
            f"e {need_complex_system} com perfil para sistemas sob medida ({free_domains} com domínio .com.br livre)."
        ),
        "total_leads": total,
        "total_analyzed": total,
        "need_new_site": need_new_site,
        "site_down_or_broken": site_down_or_broken,
        "need_complex_system": need_complex_system,
        "free_domains_count": free_domains,
        "newly_opened_count": newly_opened,
        "estimated_pipeline_brl": estimated_pipeline_min,
        "estimated_ticket_potential": f"R$ {min_fmt} a R$ {max_fmt}",
    }


def generate_outreach_scripts(
    lead: Dict[str, Any],
    xray_data: Dict[str, Any],
    score_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Gera scripts de abordagem personalizados com o diagnóstico real do Raio-X para:
    - WhatsApp (com link 1-clique wa.me)
    - E-mail (Assunto + Corpo + link mailto:)
    - Instagram DM
    - Payload estruturado (`automation_payload`) pré-pronto para o futuro robô de automação de contato.
    """
    title = (lead.get("title") or "sua empresa").strip()
    city = (lead.get("city") or "sua cidade").strip()
    reviews = int(float(lead.get("review_count") or 0))
    rating = float(lead.get("review_rating") or 0.0)
    wpp_num = (lead.get("whatsapp_clean") or normalize_whatsapp_br(lead.get("phone") or "")).strip()
    first_email = ((lead.get("emails") or "").split(",")[0]).strip()
    instagram = (lead.get("instagram") or "").strip()

    pain = score_data.get("primary_pain") or "SEM_SITE"
    service = score_data.get("recommended_service") or "SITE_NOVO"
    dom = xray_data.get("suggested_domain") or "suaempresa.com.br"
    dom_free = bool(xray_data.get("domain_available_br"))
    cms = xray_data.get("detected_cms") or "Sem Site"

    if reviews >= 10:
        social_proof = f"encontrei vocês no Google aqui em {city} (vi que são super bem avaliados, com nota {rating:.1f}!)"
    elif reviews >= 3:
        social_proof = f"encontrei a empresa de vocês no Google Maps aqui em {city}"
    else:
        social_proof = f"encontrei a {title} no Google aqui em {city}"

    if pain == "SITE_FORA_DO_AR":
        wpp_msg = (
            f"Oi, tudo bem? Falo com alguém da {title}?\n\n"
            f"Vi a empresa de vocês aqui no Google em {city} e passei pra dar um toque rápido: fui clicar no site de vocês na ficha e a página tá fora do ar dando erro.\n\n"
            f"Como o pessoal pesquisa muito por vocês na cidade, vocês estão perdendo clientes e vendas todo dia que tentam entrar e não conseguem chamar no WhatsApp.\n\n"
            f"Eu montei uma estrutura de página rápida que coloca o atendimento de vocês de volta no ar hoje mesmo. Se precisarem de ajuda para restabelecer ou colocar uma página nova no ar rapidinho, me coloco à disposição!"
        )
        email_subject = f"Aviso rápido: Site da {title} no Google Maps está fora do ar"
        ig_dm = (
            f"Opa pessoal da {title}! Vi a ficha de vocês no Google em {city} e reparei que o site tá dando erro fora do ar. "
            f"Achei legal avisar pra não perderem cliente! Se precisarem subir uma página rápida, estou por aqui."
        )
    elif pain in ("SEM_SITE", "DOMINIO_LIVRE"):
        wpp_msg = (
            f"Oi, tudo bem? É da {title}?\n\n"
            f"Vi o perfil de vocês aqui no Google em {city}, nota {rating:.1f} inclusive, muito bacana! 👏\n\n"
            f"Passei aqui porque hoje quem pesquisa pelo serviço de vocês na cidade não acha uma forma rápida de agendar ou tirar dúvidas direto no WhatsApp. A maioria acaba indo pro concorrente que aparece com botão direto.\n\n"
            f"A gente ajuda empresas e consultórios da região a lotarem o WhatsApp de clientes particulares que pesquisam no Google todo dia.\n\n"
            f"Vocês teriam interesse em receber mais clientes particulares chamando no Whats todo dia, ou a agenda já tá 100% cheia?"
        )
        email_subject = f"Mais clientes do Google no WhatsApp para {title} ({city})"
        ig_dm = (
            f"Opa pessoal da {title}! Vi o perfil top de vocês no Google em {city}. "
            f"Vocês teriam interesse em receber mais clientes particulares chamando no Whats todo dia, ou a agenda já tá cheia?"
        )
    elif pain == "OPORTUNIDADE_SISTEMA" or service == "SISTEMA_COMPLEXO":
        wpp_msg = (
            f"Oi, tudo bem? É da {title}?\n\n"
            f"Acompanhei o destaque e as avaliações da empresa de vocês aqui em {city}, parabéns pelo movimento! 🔥\n\n"
            f"Pelo volume que vocês têm, imagino que a equipe perca horas todo dia respondendo as mesmas dúvidas e agendando clientes na mão no WhatsApp.\n\n"
            f"Eu crio sistemas e automações sob medida (como agendamento online e pedidos direto no Whats) focados em desafogar o atendimento e fazer o cliente fechar sozinho em 1 minuto.\n\n"
            f"Com quem eu conseguiria bater um papo rápido de 5 minutos sobre isso?"
        )
        email_subject = f"Mais agilidade e agendamento automático para {title}"
        ig_dm = (
            f"Opa pessoal da {title}! Acompanhei o movimento de vocês em {city}. Desenvolvo sistemas e automações no WhatsApp pra desafogar atendimento e fechar agendamentos na hora — "
            f"com quem consigo trocar uma ideia rápida?"
        )
    else:
        wpp_msg = (
            f"Oi, tudo bem? É da {title}?\n\n"
            f"Vi o perfil de vocês aqui no Google em {city} e dei uma olhadinha no site de vocês ({dom}) pelo celular.\n\n"
            f"Notei 2 detalhezinhos na navegação mobile que estão fazendo clientes desistirem antes de chamar no WhatsApp ({score_data.get('pain_summary', 'layout e demora pra carregar')}). Ajustando isso, a conversão de novos clientes aumenta na hora.\n\n"
            f"Separei umas dicas práticas e um exemplo rápido de como resolver. Posso te mandar por aqui?"
        )
        email_subject = f"Ideia prática para dobrar contatos no site {dom} ({title})"
        ig_dm = (
            f"Opa pessoal da {title}! Dei uma olhada rápida no site {dom} pelo celular e notei 2 ajustes simples pra aumentar os contatos no WhatsApp. "
            f"Posso mandar por aqui?"
        )

    email_body = (
        wpp_msg
        + "\n\nSe preferir, pode responder diretamente a este e-mail ou me chamar no WhatsApp.\n\nAtenciosamente,\nDesenvolvimento Web & Tecnologia"
    )

    wpp_url = (
        f"https://wa.me/{wpp_num}?text={urllib.parse.quote(wpp_msg)}"
        if wpp_num
        else ""
    )
    mailto_url = (
        f"mailto:{first_email}?subject={urllib.parse.quote(email_subject)}&body={urllib.parse.quote(email_body)}"
        if first_email
        else ""
    )

    channels_available: List[str] = []
    if wpp_num:
        channels_available.append("whatsapp")
    if first_email:
        channels_available.append("email")
    if instagram:
        channels_available.append("instagram")

    ready_report = build_ready_report_for_lead(lead, xray_data, score_data)

    return {
        "whatsapp": wpp_msg,
        "whatsapp_url": wpp_url,
        "email_subject": email_subject,
        "email_body": email_body,
        "mailto_url": mailto_url,
        "instagram_dm": ig_dm,
        "instagram_url": instagram,
        "ready_report": ready_report,
        "automation_payload": {
            "lead_title": title,
            "city": city,
            "whatsapp_number": wpp_num,
            "email": first_email,
            "instagram": instagram,
            "primary_pain": pain,
            "recommended_service": service,
            "opportunity_score": score_data.get("opportunity_score", 0),
            "suggested_domain": dom,
            "domain_available_br": dom_free,
            "channels_available": channels_available,
        },
    }


def process_and_save_lead(
    lead_dict: Dict[str, Any],
    run_xray: bool = True,
    skip_live_network: bool = False,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Pipeline completo para um lead:
    1. Normaliza WhatsApp e faz upsert no banco SQLite
    2. Executa o Raio-X das 8 ferramentas (`run_full_xray_for_lead`)
    3. Calcula o Score de Oportunidade (`score_and_classify_lead`)
    4. Gera os Scripts de Abordagem (`generate_outreach_scripts`)
    5. Atualiza o registro no SQLite e retorna o lead completo.
    """
    if not lead_dict.get("whatsapp_clean") and lead_dict.get("phone"):
        lead_dict["whatsapp_clean"] = normalize_whatsapp_br(lead_dict["phone"])

    lead_id = upsert_lead(lead_dict, db_path=db_path)

    if run_xray:
        xray = run_full_xray_for_lead(lead_dict, skip_live_network=skip_live_network)
        score = score_and_classify_lead(lead_dict, xray)
        scripts = generate_outreach_scripts(lead_dict, xray, score)
        update_lead_xray_and_score(lead_id, xray, score, scripts, db_path=db_path)

    return get_lead(lead_id, db_path=db_path) or {}


def process_leads_batch(
    raw_leads: List[Dict[str, Any]],
    run_xray: bool = True,
    force_skip_network: bool = False,
    max_workers: int = 12,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Processa muitos leads em paralelo (Raio-X real de rede: HTTP/SSL, Registro.br RDAP, Web Archive).
    Leads simulados (`sim_*`) nunca usam rede. Falhas individuais não derrubam o lote.
    """
    from concurrent.futures import ThreadPoolExecutor

    def _one(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        is_sim = str(raw.get("place_id") or "").startswith("sim_")
        try:
            return process_and_save_lead(
                raw,
                run_xray=run_xray,
                skip_live_network=force_skip_network or is_sim,
                db_path=db_path,
            )
        except Exception:
            try:
                return process_and_save_lead(raw, run_xray=run_xray, skip_live_network=True, db_path=db_path)
            except Exception:
                return None

    if not raw_leads:
        return []
    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(raw_leads)))) as pool:
        results = list(pool.map(_one, raw_leads))
    return [r for r in results if r]
