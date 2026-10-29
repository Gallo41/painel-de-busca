import pytest
from app.services.lead_scorer import score_and_classify_lead


def test_score_lead_without_website_and_free_domain():
    lead = {
        "title": "Clínica Prime Campinas",
        "phone": "(19) 99876-5432",
        "whatsapp_clean": "5519998765432",
        "review_rating": 4.9,
        "review_count": 75,
        "niche_slug": "clinicas-odontologicas",
    }
    xray = {
        "has_website": False,
        "is_social_only_url": False,
        "site_in_air": False,
        "suggested_domain": "clinicaprimecampinas.com.br",
        "domain_available_br": True,
        "detected_cms": "Sem Site",
    }
    res = score_and_classify_lead(lead, xray)
    assert res["opportunity_score"] >= 88
    assert res["primary_pain"] in ("SEM_SITE", "DOMINIO_LIVRE")
    assert res["recommended_service"] == "SITE_NOVO"
    assert "clinicaprimecampinas.com.br" in res["pain_summary"]


def test_score_lead_with_offline_website():
    lead = {
        "title": "Advocacia Central",
        "phone": "(19) 99111-2222",
        "whatsapp_clean": "5519991112222",
        "review_rating": 4.7,
        "review_count": 40,
    }
    xray = {
        "has_website": True,
        "is_social_only_url": False,
        "site_in_air": False,
        "http_status": 0,
        "suggested_domain": "advocaciacentral.com.br",
        "domain_available_br": False,
    }
    res = score_and_classify_lead(lead, xray)
    assert res["opportunity_score"] >= 85
    assert res["primary_pain"] == "SITE_FORA_DO_AR"
    assert res["recommended_service"] == "REFORMA_SITE"


def test_score_lead_for_complex_system_expansion():
    lead = {
        "title": "Imobiliária Master Group",
        "phone": "(19) 99222-3333",
        "whatsapp_clean": "5519992223333",
        "review_rating": 4.9,
        "review_count": 150,
        "niche_slug": "imobiliarias-corretores",
    }
    xray = {
        "has_website": True,
        "is_social_only_url": False,
        "site_in_air": True,
        "has_ssl": False,
        "detected_cms": "Wix",
        "has_complex_system": False,
        "has_whatsapp_widget": False,
        "wayback_days_since_update": 900,
        "suggested_domain": "mastergroup.com.br",
        "domain_available_br": False,
    }
    res = score_and_classify_lead(lead, xray)
    assert res["opportunity_score"] >= 80
    assert res["primary_pain"] == "OPORTUNIDADE_SISTEMA"
    assert res["recommended_service"] == "SISTEMA_COMPLEXO"
