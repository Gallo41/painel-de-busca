import urllib.parse
from typing import Any, Dict, List, Optional

from app.database import get_lead, update_lead_xray_and_score, upsert_lead
from app.services.lead_scorer import score_and_classify_lead
from app.services.maps_scraper import normalize_whatsapp_br
from app.services.site_xray import run_full_xray_for_lead


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

    return {
        "whatsapp": wpp_msg,
        "whatsapp_url": wpp_url,
        "email_subject": email_subject,
        "email_body": email_body,
        "mailto_url": mailto_url,
        "instagram_dm": ig_dm,
        "instagram_url": instagram,
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
