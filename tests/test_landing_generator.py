import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.database import init_db, upsert_lead, get_landing_page_by_slug
from app.services.landing_generator import (
    build_landing_context,
    generate_landing_for_lead,
    is_eligible_for_landing,
    make_slug,
    render_landing_html,
)


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_painel.db")
    init_db(path)
    return path


def _lead(**over):
    base = {
        "title": "Clínica <Sorriso> & Cia",
        "category": "Dentista",
        "niche_slug": "odontologia",
        "city": "Piracicaba",
        "state": "SP",
        "whatsapp_clean": "5519999998888",
        "phone": "(19) 99999-8888",
        "address": "Rua A, 10",
        "review_rating": 4.8,
        "review_count": 120,
        "place_id": "pid1",
        "has_website": False,
    }
    base.update(over)
    return base


def test_make_slug_is_url_safe_and_unique_per_id():
    assert make_slug("Clínica Sorriso & Cia", 7) == "clinica-sorriso-cia-7"


def test_eligibility_no_site_or_bad_site():
    assert is_eligible_for_landing({"has_website": 0, "primary_pain": "SEM_SITE"})
    assert is_eligible_for_landing({"has_website": 1, "primary_pain": "SITE_ANTIGO"})
    assert not is_eligible_for_landing({"has_website": 1, "primary_pain": "SITE_OK"})


def test_context_has_fallback_copy_and_whatsapp_link():
    ctx = build_landing_context(_lead(), use_llm=False)
    assert ctx["whatsapp_url"].startswith("https://wa.me/5519999998888")
    assert ctx["headline"] and ctx["services"]


def test_render_escapes_html_in_lead_data():
    html = render_landing_html(build_landing_context(_lead(), use_llm=False))
    assert "<Sorriso>" not in html
    assert "&lt;Sorriso&gt;" in html
    assert "noindex" in html
    assert "Proposta de demonstra" in html


def test_generate_persists_and_regenerates_same_slug(db_path):
    lead_id = upsert_lead(_lead(), db_path=db_path)
    first = generate_landing_for_lead(lead_id, db_path=db_path, use_llm=False)
    second = generate_landing_for_lead(lead_id, db_path=db_path, use_llm=False)
    assert first["slug"] == second["slug"]
    assert get_landing_page_by_slug(first["slug"], db_path=db_path)["html"]


def test_demo_route_and_generate_endpoint(db_path):
    from app.main import create_app

    client = TestClient(create_app(db_path))
    lead_id = upsert_lead(_lead(), db_path=db_path)
    r = client.post(f"/api/leads/{lead_id}/landing?use_llm=false")
    assert r.status_code == 200
    slug = r.json()["slug"]
    page = client.get(f"/demo/{slug}")
    assert page.status_code == 200 and "text/html" in page.headers["content-type"]
    assert client.get("/demo/nao-existe").status_code == 404
    assert client.post("/api/leads/99999/landing").status_code == 404
