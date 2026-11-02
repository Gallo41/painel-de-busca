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
    # Garantir que as 8 ferramentas não são links clicáveis externos (href="https://...")
    assert 'href="https://www.google.com/maps"' not in html
    assert 'href="https://builtwith.com"' not in html
    assert 'href="https://www.wappalyzer.com"' not in html
    assert 'href="https://whatcms.org"' not in html
    assert 'href="https://web.archive.org"' not in html
    assert "embedded-maps-box" in html
    assert "embedded-builtwith-box" in html
    assert "embedded-wappalyzer-box" in html
    assert "embedded-whatcms-box" in html
    assert "embedded-wayback-box" in html
    assert 'data-theme="dark"' in html
    assert 'id="theme-toggle"' in html

    r_css = client.get("/static/styles.css")
    assert r_css.status_code == 200
    assert 'data-theme="dark"' in r_css.text

    r_js = client.get("/static/app.js")
    assert r_js.status_code == 200
    assert "/api/jobs" in r_js.text
    assert "/api/outreach/enqueue" in r_js.text
    assert "toggleTheme" in r_js.text
    assert 'stat-total' in r_js.text
    assert 'stat-without-site' in r_js.text
    assert 'stat-site-down' in r_js.text
    assert 'stat-complex' in r_js.text
    assert 'stat-domain-free' in r_js.text
    assert 'kpi-total' not in r_js.text


def test_dashboard_pagination_elements_present(client):
    r_index = client.get("/")
    assert r_index.status_code == 200
    html = r_index.text
    assert 'id="pagination-bar"' in html
    assert 'id="page-size-select"' in html
    assert 'id="btn-prev-page"' in html
    assert 'id="btn-next-page"' in html
    assert 'id="pagination-pages"' in html
    assert 'id="page-info"' in html

    r_css = client.get("/static/styles.css")
    assert r_css.status_code == 200
    assert ".pagination-bar" in r_css.text
    assert ".btn-page-num" in r_css.text
    assert ".pagination-pages" in r_css.text

    r_js = client.get("/static/app.js")
    assert r_js.status_code == 200
    assert "renderPagination" in r_js.text
    assert "goToPage" in r_js.text
    assert "onPageSizeChange" in r_js.text
    assert "buildPaginationButtons" in r_js.text


def test_dashboard_decision_status_elements_present(client):
    r_index = client.get("/")
    assert r_index.status_code == 200
    html = r_index.text
    assert "filter-hide-ignored" in html
    assert "Decisão" in html
    assert "vou_fazer" in html
    assert "nao_fazer" in html
    assert "decision-filter-strip" in html
    assert "filter-search-inline" in html
    assert "count-status-vou" in html
    assert "btn-clear-filters" in html

    r_css = client.get("/static/styles.css")
    assert r_css.status_code == 200
    assert ".lead-status-select" in r_css.text
    assert ".btn-decision" in r_css.text
    assert ".status-vou-fazer" in r_css.text
    assert ".status-nao-fazer" in r_css.text
    assert ".decision-pill-btn" in r_css.text
    assert ".inline-search-wrap" in r_css.text

    r_js = client.get("/static/app.js")
    assert r_js.status_code == 200
    assert "quickUpdateLeadStatus" in r_js.text
    assert "normStatus" in r_js.text
    assert "renderDecisionButtons" in r_js.text
    assert "setStatusFilter" in r_js.text
    assert "clearAllFilters" in r_js.text
    assert "onInlineSearch" in r_js.text


