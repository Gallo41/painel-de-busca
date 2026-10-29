import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_ui.db")
    monkeypatch.setenv("PAINEL_DB_PATH", db_file)
    from app.main import create_app

    app = create_app(db_path=db_file)
    with TestClient(app) as c:
        yield c


def test_dashboard_html_and_assets_served(client):
    r_index = client.get("/")
    assert r_index.status_code == 200
    html = r_index.text
    assert "Selecionar Nichos" in html
    assert "achar o negócio" in html.lower()
    assert "raio x do site atual" in html.lower()
    assert "registro.br" in html.lower()
    assert "builtwith.com" in html.lower()
    assert "web.archive.org" in html.lower()
    assert "Central de Contato" in html

    r_css = client.get("/static/styles.css")
    assert r_css.status_code == 200

    r_js = client.get("/static/app.js")
    assert r_js.status_code == 200
    assert "/api/jobs" in r_js.text
    assert "/api/outreach/enqueue" in r_js.text
