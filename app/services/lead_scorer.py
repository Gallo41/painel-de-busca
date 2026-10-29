from typing import Any, Dict

COMPLEX_SYSTEM_NICHES = {
    "clinicas-odontologicas",
    "clinicas-veterinarias-pet",
    "escritorios-advocacia",
    "contabilidade-consultoria",
    "imobiliarias-corretores",
    "restaurantes-buffets-eventos",
}


def score_and_classify_lead(lead: Dict[str, Any], xray_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula o Score de Oportunidade (0 a 100), classifica a Dor Principal (`primary_pain`)
    e define o Serviço Recomendado (`SITE_NOVO`, `REFORMA_SITE` ou `SISTEMA_COMPLEXO`).
    """
    has_site = bool(xray_data.get("has_website"))
    is_social = bool(xray_data.get("is_social_only_url"))
    site_in_air = bool(xray_data.get("site_in_air"))
    dom_free = bool(xray_data.get("domain_available_br"))
    suggested_dom = xray_data.get("suggested_domain") or "empresa.com.br"
    cms = xray_data.get("detected_cms") or "Sem Site"
    has_ssl = bool(xray_data.get("has_ssl"))
    has_wpp = bool(xray_data.get("has_whatsapp_widget"))
    has_complex = bool(xray_data.get("has_complex_system"))
    days_old = xray_data.get("wayback_days_since_update")

    reviews = int(float(lead.get("review_count") or 0))
    has_contact = bool(lead.get("whatsapp_clean") or lead.get("phone") or lead.get("emails") or lead.get("instagram"))
    niche_slug = (lead.get("niche_slug") or "").strip()
    is_new_company = (lead.get("source") == "casadosdados") or str(lead.get("opened_date", "")).startswith(("2025", "2026"))

    contact_bonus = 6 if has_contact else 0
    reviews_bonus = 6 if reviews >= 30 else (3 if reviews >= 10 else 0)

    # Caso 1: Tem site próprio cadastrado no Google Maps, mas está FORA DO AR (DownForEveryoneOrJustMe)
    if has_site and not is_social and not site_in_air:
        score = min(99, 84 + contact_bonus + reviews_bonus)
        return {
            "opportunity_score": score,
            "primary_pain": "SITE_FORA_DO_AR",
            "recommended_service": "REFORMA_SITE",
            "pain_summary": (
                f"Site cadastrado no Google Maps está FORA DO AR (erro de conexão/DNS). "
                f"Empresa ativa com {reviews} avaliações perdendo clientes que clicam no link."
            ),
        }

    # Caso 2: Não tem site próprio ou usa apenas Linktree / Instagram como "site"
    if (not has_site) or is_social:
        base = 76
        if dom_free:
            base += 11
        if is_new_company:
            base += 4
        score = min(98, base + contact_bonus + reviews_bonus)
        primary_pain = "DOMINIO_LIVRE" if (is_social and dom_free) else "SEM_SITE"

        if is_social:
            summary = (
                f"Usa apenas {cms} no lugar de um site profissional"
                + (f" e o domínio {suggested_dom} está LIVRE no Registro.br." if dom_free else ".")
            )
        elif is_new_company:
            summary = (
                f"Empresa recém-aberta (CNPJ ativo) ainda sem site próprio"
                + (f" — domínio {suggested_dom} LIVRE no Registro.br!" if dom_free else ".")
            )
        else:
            summary = (
                f"Negócio consolidado ({reviews} avaliações no Maps) sem site próprio"
                + (f" e com o domínio {suggested_dom} LIVRE no Registro.br!" if dom_free else ".")
            )

        return {
            "opportunity_score": score,
            "primary_pain": primary_pain,
            "recommended_service": "SITE_NOVO",
            "pain_summary": summary,
        }

    # Caso 3: Tem site no ar — verificar potencial de Expansão para Sistema Mais Complexo ou Reforma Técnica
    weaknesses = []
    tech_penalty = 0
    if cms in ("Wix", "Joomla", "Loja Integrada"):
        weaknesses.append(f"construído em {cms}")
        tech_penalty += 8
    if not has_ssl:
        weaknesses.append("sem certificado HTTPS/SSL (aviso de 'Não Seguro')")
        tech_penalty += 8
    if not has_wpp:
        weaknesses.append("sem botão rápido de WhatsApp")
        tech_penalty += 5
    if days_old and days_old >= 365:
        anos = max(1, round(days_old / 365))
        weaknesses.append(f"sem atualização relevante há ~{anos} ano(s) no Web Archive")
        tech_penalty += 7

    # Se a empresa tem bom porte (muitas avaliações ou nicho de sistema) e não possui sistema online (portal/agenda/catálogo)
    if (reviews >= 40 or niche_slug in COMPLEX_SYSTEM_NICHES) and not has_complex:
        score = min(95, 72 + tech_penalty + contact_bonus + reviews_bonus)
        extra_flaws = f" (além de ser {', '.join(weaknesses)})" if weaknesses else ""
        return {
            "opportunity_score": score,
            "primary_pain": "OPORTUNIDADE_SISTEMA",
            "recommended_service": "SISTEMA_COMPLEXO",
            "pain_summary": (
                f"Empresa de porte ({reviews} avaliações) com site meramente estático sem sistema integrado "
                f"(agendamento online, portal do cliente ou catálogo dinâmico){extra_flaws}."
            ),
        }

    if weaknesses:
        score = min(92, 66 + tech_penalty + contact_bonus + reviews_bonus)
        return {
            "opportunity_score": score,
            "primary_pain": "SITE_AMADOR_ANTIGO",
            "recommended_service": "REFORMA_SITE",
            "pain_summary": f"Site atual precisa de modernização: {', '.join(weaknesses)}.",
        }

    # Site saudável, mas ainda pode receber oferta de automação/sistema complementar
    score = min(75, 52 + contact_bonus + reviews_bonus)
    return {
        "opportunity_score": score,
        "primary_pain": "OPORTUNIDADE_SISTEMA",
        "recommended_service": "SISTEMA_COMPLEXO",
        "pain_summary": "Presença web básica estruturada; potencial para oferecer automações, integrações ou sistemas sob medida.",
    }
