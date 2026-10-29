import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_api.db")
    monkeypatch.setenv("PAINEL_DB_PATH", db_file)
    from app.main import create_app

    app = create_app(db_path=db_file)
    with TestClient(app) as c:
        yield c


def test_get_niches_and_health(client):
    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    data = r_health.json()
    assert "stats" in data
    assert "scraper_engine" in data

    r_niches = client.get("/api/niches")
    assert r_niches.status_code == 200
    niches = r_niches.json()
    assert len(niches) >= 10


def test_run_search_job_and_filter_leads(client):
    r_job = client.post(
        "/api/jobs",
        json={
            "city": "Campinas",
            "state": "SP",
            "niche_slugs": ["clinicas-odontologicas", "imobiliarias-corretores"],
            "depth": 5,
            "grid_size": 1,
            "include_socials": True,
            "run_xray": True,
            "source_mode": "demo",
        },
    )
    assert r_job.status_code == 200
    job_res = r_job.json()
    assert job_res["job"]["status"] == "completed"
    assert job_res["total_leads_processed"] >= 6

    r_leads = client.get("/api/leads?city=Campinas")
    assert r_leads.status_code == 200
    leads = r_leads.json()
    assert len(leads) >= 6

    first_id = leads[0]["id"]
    # Atribuir lead para 'amigo' e mudar status
    r_patch = client.patch(
        f"/api/leads/{first_id}",
        json={"assigned_to": "amigo", "lead_status": "analisado", "notes": "Excelente clínica sem site"},
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["assigned_to"] == "amigo"


def test_outreach_automation_endpoints(client):
    # Cria um lead manual
    r_create = client.post(
        "/api/leads",
        json={
            "title": "Clínica Vida Nova",
            "category": "Clínica Médica",
            "phone": "(19) 99888-7766",
            "emails": "contato@vidanova.com.br",
            "website": "",
            "city": "Campinas",
            "state": "SP",
            "niche_slug": "clinicas-odontologicas",
            "review_rating": 4.9,
            "review_count": 48,
            "run_xray": True,
        },
    )
    assert r_create.status_code == 200
    lead = r_create.json()
    lead_id = lead["id"]

    # Enfileira para o bot futuro de WhatsApp
    r_enq = client.post(
        "/api/outreach/enqueue",
        json={"lead_ids": [lead_id], "channels": ["whatsapp"]},
    )
    assert r_enq.status_code == 200
    assert r_enq.json()["enqueued_count"] == 1

    # Worker reclama o próximo disparo da fila
    r_claim = client.post(
        "/api/outreach/claim",
        json={"channel": "whatsapp", "worker_id": "bot-evolution-01"},
    )
    assert r_claim.status_code == 200
    claimed = r_claim.json()["item"]
    assert claimed["lead_id"] == lead_id
    assert claimed["status"] == "sending"

    # Webhook confirma envio
    r_status = client.patch(
        f"/api/outreach/{claimed['id']}/status",
        json={"status": "sent", "external_message_id": "evo_msg_001"},
    )
    assert r_status.status_code == 200
    assert r_status.json()["status"] == "sent"

    # Verifica que o lead mudou automaticamente para 'contatado'
    r_lead_after = client.get(f"/api/leads/{lead_id}")
    assert r_lead_after.json()["lead_status"] == "contatado"
