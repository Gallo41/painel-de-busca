import pytest
from app.services.outreach_generator import generate_outreach_scripts, process_and_save_lead
from app.database import init_db


def test_generate_outreach_scripts_for_missing_site_and_free_domain():
    lead = {
        "title": "Odonto Prime Campinas",
        "city": "Campinas",
        "phone": "(19) 99876-5432",
        "whatsapp_clean": "5519998765432",
        "emails": "contato@odontoprime.com.br",
        "instagram": "https://instagram.com/odontoprime",
        "review_rating": 4.9,
        "review_count": 82,
    }
    xray = {
        "has_website": False,
        "is_social_only_url": False,
        "site_in_air": False,
        "suggested_domain": "odontoprimecampinas.com.br",
        "domain_available_br": True,
        "detected_cms": "Sem Site",
    }
    score = {
        "opportunity_score": 95,
        "primary_pain": "SEM_SITE",
        "recommended_service": "SITE_NOVO",
        "pain_summary": "Sem site próprio e domínio odontoprimecampinas.com.br livre no Registro.br",
    }
    scripts = generate_outreach_scripts(lead, xray, score)
    assert "Odonto Prime Campinas" in scripts["whatsapp"]
    assert "link" not in scripts["whatsapp"].lower()
    assert "clientes" in scripts["whatsapp"].lower()
    assert scripts["whatsapp_url"].startswith("https://wa.me/5519998765432?text=")
    assert "Odonto Prime Campinas" in scripts["instagram_dm"]
    assert "whatsapp" in scripts["automation_payload"]["channels_available"]


def test_generate_outreach_scripts_for_complex_system():
    lead = {
        "title": "Imobiliária Master Group",
        "city": "Campinas",
        "phone": "(19) 99111-2222",
        "whatsapp_clean": "5519991112222",
        "review_rating": 4.8,
        "review_count": 140,
        "niche_slug": "imobiliarias-corretores",
    }
    xray = {
        "has_website": True,
        "is_social_only_url": False,
        "site_in_air": True,
        "suggested_domain": "mastergroup.com.br",
        "domain_available_br": False,
        "detected_cms": "Wix",
        "has_complex_system": False,
    }
    score = {
        "opportunity_score": 88,
        "primary_pain": "OPORTUNIDADE_SISTEMA",
        "recommended_service": "SISTEMA_COMPLEXO",
        "pain_summary": "Empresa de porte sem sistema integrado",
    }
    scripts = generate_outreach_scripts(lead, xray, score)
    assert "sistema" in scripts["whatsapp"].lower() or "automação" in scripts["whatsapp"].lower()
    assert scripts["automation_payload"]["recommended_service"] == "SISTEMA_COMPLEXO"


def test_generate_outreach_scripts_humanized_tone_all_scenarios():
    base_lead = {
        "title": "Oficina do João",
        "city": "Piracicaba",
        "phone": "(19) 98765-4321",
        "whatsapp_clean": "5519987654321",
        "emails": "contato@oficinadojoao.com.br",
        "review_rating": 4.8,
        "review_count": 45,
    }

    # 1. Site fora do ar
    xray_down = {"has_website": True, "site_in_air": False, "suggested_domain": "oficinadojoao.com.br"}
    score_down = {"primary_pain": "SITE_FORA_DO_AR", "recommended_service": "RECUPERAR_SITE"}
    sc_down = generate_outreach_scripts(base_lead, xray_down, score_down)
    assert "Oi, tudo bem? Falo com alguém da Oficina do João?" in sc_down["whatsapp"]
    assert "fora do ar" in sc_down["whatsapp"]
    assert "Olá, equipe da" not in sc_down["whatsapp"]  # Garante ausência de tom robótico

    # 2. Sem site com domínio livre
    xray_nosite = {"has_website": False, "domain_available_br": True, "suggested_domain": "oficinadojoao.com.br"}
    score_nosite = {"primary_pain": "SEM_SITE", "recommended_service": "SITE_NOVO"}
    sc_nosite = generate_outreach_scripts(base_lead, xray_nosite, score_nosite)
    assert "Oi, tudo bem? É da Oficina do João?" in sc_nosite["whatsapp"]
    assert "link" not in sc_nosite["whatsapp"].lower()
    assert "clientes" in sc_nosite["whatsapp"].lower()
    assert "agenda" in sc_nosite["whatsapp"].lower()
    assert "Olá, equipe da" not in sc_nosite["whatsapp"]

    # 3. Melhoria de site mobile
    xray_slow = {"has_website": True, "site_in_air": True, "suggested_domain": "oficinadojoao.com.br"}
    score_slow = {"primary_pain": "SITE_LENTO", "recommended_service": "OTIMIZACAO_SITE", "pain_summary": "lento no 4G"}
    sc_slow = generate_outreach_scripts(base_lead, xray_slow, score_slow)
    assert "Oi, tudo bem? É da Oficina do João?" in sc_slow["whatsapp"]
    assert "Posso te mandar por aqui?" in sc_slow["whatsapp"]
    assert "Olá, equipe da" not in sc_slow["whatsapp"]


def test_process_and_save_lead_pipeline(tmp_path):
    db_path = str(tmp_path / "test_pipeline.db")
    init_db(db_path)
    saved = process_and_save_lead(
        {
            "place_id": "pipe_1",
            "title": "Clínica Sorriso Real",
            "city": "Campinas",
            "state": "SP",
            "phone": "(19) 99888-1122",
            "whatsapp_clean": "5519998881122",
            "website": "",
            "review_rating": 4.9,
            "review_count": 55,
            "niche_slug": "clinicas-odontologicas",
        },
        skip_live_network=True,
        db_path=db_path,
    )
    assert saved["id"] > 0
    assert saved["opportunity_score"] >= 80
    assert saved["outreach_scripts"]["whatsapp_url"].startswith("https://wa.me/5519998881122")
