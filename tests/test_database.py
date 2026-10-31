import os
import tempfile
import pytest

from app.database import (
    init_db,
    upsert_niches,
    list_niches,
    create_search_job,
    update_search_job,
    get_search_job,
    list_search_jobs,
    upsert_lead,
    update_lead_xray_and_score,
    update_lead_management,
    get_lead,
    list_leads,
    get_dashboard_stats,
    enqueue_outreach,
    list_outreach_queue,
    claim_next_outreach,
    update_outreach_status,
)


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_painel.db")
    init_db(path)
    return path


def test_niches_crud(db_path):
    sample_niches = [
        {
            "slug": "clinicas-odontologicas",
            "name": "Clínicas Odontológicas e Dentistas",
            "category_group": "Saúde & Estética",
            "search_terms": ["dentista", "clínica odontológica"],
            "cnae_codes": ["8630-5/04"],
            "recommended_offer": "SISTEMA_COMPLEXO",
            "description": "Alto ticket, precisam de landing page e sistema de agendamento.",
        }
    ]
    upsert_niches(sample_niches, db_path=db_path)
    niches = list_niches(db_path=db_path)
    assert len(niches) == 1
    assert niches[0]["slug"] == "clinicas-odontologicas"
    assert "dentista" in niches[0]["search_terms"]
    assert niches[0]["recommended_offer"] == "SISTEMA_COMPLEXO"


def test_search_jobs_lifecycle(db_path):
    job_id = create_search_job(
        city="Campinas",
        state="SP",
        niche_slugs=["clinicas-odontologicas"],
        keywords=["dentista em Campinas SP"],
        depth=5,
        grid_size=1,
        include_socials=True,
        source_mode="google_maps",
        db_path=db_path,
    )
    job = get_search_job(job_id, db_path=db_path)
    assert job is not None
    assert job["city"] == "Campinas"
    assert job["status"] == "pending"

    update_search_job(job_id, status="completed", total_found=14, db_path=db_path)
    updated = get_search_job(job_id, db_path=db_path)
    assert updated["status"] == "completed"
    assert updated["total_found"] == 14

    jobs = list_search_jobs(db_path=db_path)
    assert len(jobs) == 1


def test_leads_deduplication_and_filtering(db_path):
    lead1_id = upsert_lead(
        {
            "place_id": "place_123",
            "title": "Odonto Prime Campinas",
            "category": "Dentista",
            "phone": "(19) 99876-5432",
            "whatsapp_clean": "5519998765432",
            "emails": "contato@odontoprime.com.br",
            "website": "",
            "address": "Av. Brasil, 100 - Campinas, SP",
            "city": "Campinas",
            "state": "SP",
            "niche_slug": "clinicas-odontologicas",
            "review_rating": 4.9,
            "review_count": 85,
            "instagram": "https://instagram.com/odontoprime",
            "source": "google_maps",
        },
        db_path=db_path,
    )
    # Second upsert with same place_id should update existing record, not duplicate
    lead1_id_again = upsert_lead(
        {
            "place_id": "place_123",
            "title": "Odonto Prime Campinas",
            "category": "Dentista",
            "phone": "(19) 99876-5432",
            "whatsapp_clean": "5519998765432",
            "emails": "contato@odontoprime.com.br",
            "website": "",
            "address": "Av. Brasil, 100 - Campinas, SP",
            "city": "Campinas",
            "state": "SP",
            "niche_slug": "clinicas-odontologicas",
            "review_rating": 4.9,
            "review_count": 90,
            "instagram": "https://instagram.com/odontoprime",
            "source": "google_maps",
        },
        db_path=db_path,
    )
    assert lead1_id == lead1_id_again

    update_lead_xray_and_score(
        lead1_id,
        xray_data={
            "has_website": False,
            "is_social_only_url": False,
            "site_in_air": False,
            "http_status": 0,
            "has_ssl": False,
            "suggested_domain": "odontoprimecampinas.com.br",
            "domain_available_br": True,
            "detected_cms": "Sem Site",
            "tech_stack": [],
            "has_whatsapp_widget": False,
            "has_analytics_pixel": False,
            "is_mobile_friendly": False,
            "has_complex_system": False,
            "wayback_first_seen": None,
            "wayback_last_seen": None,
            "external_tools_links": {"registro_br": "https://registro.br"},
        },
        score_data={
            "opportunity_score": 95,
            "primary_pain": "SEM_SITE",
            "recommended_service": "SITE_NOVO",
            "pain_summary": "Sem site próprio e domínio odontoprimecampinas.com.br livre no Registro.br",
        },
        outreach_scripts={
            "whatsapp": "Olá Odonto Prime!",
            "email_subject": "Domínio odontoprimecampinas.com.br",
            "email_body": "Corpo do email",
            "instagram_dm": "Oi pessoal da Odonto Prime!",
        },
        db_path=db_path,
    )

    update_lead_management(
        lead1_id,
        assigned_to="eu",
        lead_status="contatado",
        notes="Mandei WhatsApp às 14h",
        db_path=db_path,
    )

    lead = get_lead(lead1_id, db_path=db_path)
    assert lead["opportunity_score"] == 95
    assert lead["primary_pain"] == "SEM_SITE"
    assert lead["domain_available_br"] is True
    assert lead["assigned_to"] == "eu"
    assert lead["lead_status"] == "contatado"
    assert lead["outreach_scripts"]["whatsapp"] == "Olá Odonto Prime!"

    filtered = list_leads(primary_pain="SEM_SITE", assigned_to="eu", min_score=80, db_path=db_path)
    assert len(filtered) == 1

    stats = get_dashboard_stats(db_path=db_path)
    assert stats["total_leads"] == 1
    assert stats["without_site"] == 1
    assert stats["domain_available"] == 1


def test_outreach_queue_idempotency_and_claim(db_path):
    lead_id = upsert_lead(
        {
            "place_id": "place_999",
            "title": "Advocacia Silva",
            "phone": "11988887777",
            "whatsapp_clean": "5511988887777",
            "city": "São Paulo",
        },
        db_path=db_path,
    )
    q1 = enqueue_outreach(
        lead_id=lead_id,
        channel="whatsapp",
        recipient="5511988887777",
        subject="",
        message_body="Olá Dr. Silva, vi que o site está fora do ar.",
        diagnostic_context={"primary_pain": "SITE_FORA_DO_AR"},
        db_path=db_path,
    )
    q2 = enqueue_outreach(
        lead_id=lead_id,
        channel="whatsapp",
        recipient="5511988887777",
        subject="",
        message_body="Mensagem atualizada.",
        diagnostic_context={"primary_pain": "SITE_FORA_DO_AR"},
        db_path=db_path,
    )
    assert q1 == q2

    queue = list_outreach_queue(status="ready", db_path=db_path)
    assert len(queue) == 1
    assert queue[0]["message_body"] == "Mensagem atualizada."

    claimed = claim_next_outreach(channel="whatsapp", worker_id="bot-wpp-1", db_path=db_path)
    assert claimed is not None
    assert claimed["id"] == q1
    assert claimed["status"] == "sending"

    update_outreach_status(
        q1,
        status="sent",
        external_message_id="wamid.12345",
        webhook_response={"ack": 1},
        db_path=db_path,
    )
    sent_items = list_outreach_queue(status="sent", db_path=db_path)
    assert len(sent_items) == 1
    assert sent_items[0]["external_message_id"] == "wamid.12345"


def test_multicriteria_deduplication_and_enrichment(db_path):
    from app.database import (
        normalize_business_title,
        upsert_lead,
        get_lead,
        deduplicate_existing_leads_db,
        get_connection,
    )

    # 1. Normalização de título
    assert normalize_business_title("Ello Próteses e Implantes") == "ello proteses e implantes"
    assert normalize_business_title("Encanttá Odontologia | Implante Dentário - Alto") == "encantta odontologia implante dentario alto"

    # 2. Inserção inicial sem place_id
    id1 = upsert_lead(
        {
            "title": "Ello Próteses e Implantes",
            "city": "Piracicaba",
            "phone": "(19)99716-6254",
            "whatsapp_clean": "5519997166254",
            "place_id": "",
            "category": "",
            "review_count": 1250,
        },
        db_path=db_path,
    )

    # 3. Segunda inserção com place_id e telefone formatado com espaço
    id2 = upsert_lead(
        {
            "title": "Ello Próteses e Implantes",
            "city": "Piracicaba",
            "phone": "(19) 99716-6254",
            "whatsapp_clean": "5519997166254",
            "place_id": "ChIJ386f9FMwxpQRevR19E-D3Ts",
            "category": "Dentista",
            "review_count": 1253,
        },
        db_path=db_path,
    )
    assert id1 == id2

    saved = get_lead(id1, db_path=db_path)
    assert saved["place_id"] == "ChIJ386f9FMwxpQRevR19E-D3Ts"
    assert saved["category"] == "Dentista"
    assert saved["review_count"] == 1253

    # 4. Inserção manual de duplicata forçada para testar deduplicate_existing_leads_db
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO leads (title, city, state, phone, whatsapp_clean, dedupe_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("Ello Próteses e Implantes", "Piracicaba", "SP", "(19) 99716-6254", "5519997166254", "dup:test:123"),
        )
    
    deleted = deduplicate_existing_leads_db(db_path=db_path)
    assert deleted >= 1
    with get_connection(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM leads WHERE title LIKE '%Ello%'").fetchone()[0]
        assert count == 1
