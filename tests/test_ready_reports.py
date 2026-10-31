import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_ready_reports.db")
    monkeypatch.setenv("PAINEL_DB_PATH", db_file)
    from app.main import create_app

    app = create_app(db_path=db_file)
    with TestClient(app) as c:
        yield c


def test_piracicaba_search_job_no_charmap_error_and_ready_reports(client):
    """
    Garante que buscar Piracicaba-SP funciona sem erro 'charmap' codec no Windows
    e entrega tanto o Resumo Executivo quanto as Fichas de Relatório Prontas.
    """
    r_job = client.post(
        "/api/jobs",
        json={
            "city": "Piracicaba",
            "state": "SP",
            "niche_slugs": ["clinicas-odontologicas", "escritorios-advocacia"],
            "depth": 5,
            "grid_size": 1,
            "include_socials": True,
            "run_xray": True,
            "source_mode": "auto",
            "skip_live_network": True,
        },
    )
    assert r_job.status_code == 200, r_job.text
    job_data = r_job.json()
    assert job_data["total_leads_processed"] >= 2
    assert "executive_summary" in job_data
    exec_sum = job_data["executive_summary"]
    assert "Piracicaba" in exec_sum["headline"]
    assert "R$" in exec_sum["estimated_ticket_potential"]

    # Valida GET /api/reports/summary
    r_sum = client.get("/api/reports/summary?city=Piracicaba")
    assert r_sum.status_code == 200
    sum_data = r_sum.json()
    assert sum_data["total_leads"] >= 2

    # Valida que cada lead vem com outreach_scripts.ready_report mastigado
    r_leads = client.get("/api/leads?search_query=Piracicaba")
    assert r_leads.status_code == 200
    leads = r_leads.json()
    assert len(leads) >= 2

    for lead in leads:
        sc = lead.get("outreach_scripts") or {}
        assert "ready_report" in sc
        rr = sc["ready_report"]
        assert rr.get("what_to_sell")
        assert "R$" in rr.get("ticket_range", "")
        assert rr.get("executive_pitch")
        bullets = rr.get("bullets") or []
        assert len(bullets) == 4
        labels = [b["label"] for b in bullets]
        assert any("Google Maps" in lbl for lbl in labels)
        assert any("Registro.br" in lbl for lbl in labels)


def test_live_maps_scrape_piracicaba_utf8_safe():
    """
    Valida que run_live_maps_scrape executa sem UnicodeEncodeError ('charmap')
    mesmo quando o container Docker gmaps-scraper está ativo na porta 8080.
    """
    from app.services.maps_scraper import run_live_maps_scrape

    leads = run_live_maps_scrape(
        city="Piracicaba",
        state="SP",
        niche_slugs=["clinicas-odontologicas"],
        depth=5,
        grid_size=1,
    )
    assert isinstance(leads, list)
    assert len(leads) >= 1
    assert leads[0]["city"] == "Piracicaba"
