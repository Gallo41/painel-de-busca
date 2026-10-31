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
        alt_str = f" (Opções extras: {', '.join(variations[1:3])})" if len(variations) > 1 else ""
        bullet_domain = f"Domínio {dom} está LIVRE no Registro.br para você registrar pro cliente!{alt_str}"
    else:
        alt_str = f" — mas {', '.join(variations[1:3])} estão LIVRES" if len(variations) > 1 else ""
        bullet_domain = f"Domínio {dom} já existe no Registro.br{alt_str}."

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

    return {
        "headline": headline,
        "what_to_sell": what_to_sell,
        "ticket_range": ticket_range,
        "category_tab": category_tab,
        "bullets": {
            "maps_and_cnpj": bullet_maps_cnpj,
            "domain_registro_br": bullet_domain,
            "site_health_and_history": bullet_health,
            "tech_and_systems": bullet_tech,
        },
        "missing_opportunities": missing_opps[:4],
    }


def build_executive_summary_report(leads: List[Dict[str, Any]], city: str = "") -> Dict[str, Any]:
    """Consolida os números do Relatório Executivo Pronto para exibição imediata no topo da página."""
    total = len(leads)
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

    return {
        "city": city or (leads[0].get("city") if leads else "Todas as Cidades"),
        "total_analyzed": total,
        "need_new_site": need_new_site,
        "site_down_or_broken": site_down_or_broken,
        "need_complex_system": need_complex_system,
        "free_domains_count": free_domains,
        "newly_opened_count": newly_opened,
        "estimated_pipeline_brl": estimated_pipeline_min,
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

    social_proof = (
        f"vi que vocês têm {reviews} avaliações (nota {rating:.1f}) no Google Maps em {city}"
        if reviews >= 5
        else f"encontrei a {title} aqui em {city}"
    )

    if pain == "SITE_FORA_DO_AR":
        wpp_msg = (
            f"Olá, pessoal da {title}! Tudo bem?\n\n"
            f"Sou desenvolvedor web e {social_proof}. Tentei acessar o site de vocês cadastrado no Maps agora há pouco e notei que ele está fora do ar (dando erro de conexão para quem clica).\n\n"
            f"Vocês já estão sabendo dessa queda? Se quiserem, consigo ajudar vocês a colocar um site novo/moderno no ar rapidinho para não perderem os clientes que vêm pelo Google."
        )
        email_subject = f"Aviso rápido: Site da {title} no Google Maps está fora do ar"
        ig_dm = (
            f"Olá pessoal da {title}! Vi vocês no Google Maps em {city} e notei que o link do site de vocês lá está fora do ar. "
            f"Trabalho com desenvolvimento de sites e sistemas — posso mandar uma ideia rápida de como resolver?"
        )
    elif pain in ("SEM_SITE", "DOMINIO_LIVRE"):
        dom_line = (
            f"Inclusive consultei no Registro.br e vi que o domínio oficial *{dom}* ainda está livre hoje para registro."
            if dom_free
            else f"Vi que hoje vocês concentram o link apenas em {cms if xray_data.get('is_social_only_url') else 'redes sociais'}."
        )
        wpp_msg = (
            f"Olá, equipe da {title}! Tudo bem?\n\n"
            f"Sou desenvolvedor de sites e sistemas e {social_proof}, mas notei que vocês ainda não têm um site próprio conectado na ficha do Google.\n\n"
            f"{dom_line}\n\n"
            f"Eu e meu sócio montamos uma prévia de como ficaria uma página profissional da {title} focada em trazer clientes direto pro WhatsApp. Posso te mandar o link sem compromisso?"
        )
        email_subject = (
            f"Domínio {dom} disponível + Presença no Google para {title}"
            if dom_free
            else f"Estrutura de Site Profissional para {title} ({city})"
        )
        ig_dm = (
            f"Oi pessoal da {title}! Vi o perfil de vocês no Google Maps ({reviews} avaliações!) e notei que o domínio {dom} está livre e vocês ainda não têm site próprio lá. "
            f"Posso mostrar um modelo rápido que criamos pro segmento de vocês?"
        )
    elif pain == "OPORTUNIDADE_SISTEMA" or service == "SISTEMA_COMPLEXO":
        wpp_msg = (
            f"Olá, equipe da {title}! Tudo bem?\n\n"
            f"Eu e meu sócio trabalhamos com desenvolvimento de sistemas web e sites sob medida. {social_proof.capitalize()} e analisamos a presença digital atual de vocês.\n\n"
            f"Pelo porte da {title}, notamos uma oportunidade grande de automatizar o atendimento/captação com um sistema integrado (como agendamento online, área de cliente ou catálogo inteligente) conectado direto ao WhatsApp.\n\n"
            f"Faz sentido conversarmos 5 minutinhos para eu mostrar como aplicamos isso no setor de vocês?"
        )
        email_subject = f"Modernização Digital & Sistema Sob Medida para {title}"
        ig_dm = (
            f"Olá equipe da {title}! Acompanhei o destaque de vocês em {city} ({reviews} avaliações no Maps) e desenvolvemos sistemas sob medida e portais modernos para o segmento de vocês. "
            f"Com quem consigo falar sobre parcerias/tecnologia?"
        )
    else:
        wpp_msg = (
            f"Olá, equipe da {title}! Tudo bem?\n\n"
            f"Sou desenvolvedor web e {social_proof}. Fizemos um raio-x técnico rápido no site atual de vocês ({dom}) e notamos alguns pontos que estão travando conversões no celular ({score_data.get('pain_summary', 'layout e velocidade')}).\n\n"
            f"Posso te enviar um resumo gratuito em 3 tópicos do que dá pra melhorar nele?"
        )
        email_subject = f"Raio-X Técnico do site {dom} ({title})"
        ig_dm = (
            f"Oi equipe da {title}! Fizemos uma análise rápida do site {dom} e encontramos melhorias importantes de conversão mobile e segurança. "
            f"Posso mandar o diagnóstico rápido por aqui ou no WhatsApp?"
        )

    email_body = wpp_msg + "\n\nAtenciosamente,\nConsultoria de Desenvolvimento Web & Sistemas"

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
