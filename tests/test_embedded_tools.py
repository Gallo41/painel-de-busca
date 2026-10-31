from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_tool_maps_engine_and_geocoding():
    res = client.get("/api/tools/maps-engine?city=Campinas&state=SP&grid_size=2")
    assert res.status_code == 200
    data = res.json()
    assert "engine" in data
    assert "geocoding" in data
    assert data["geocoding"]["city"] == "Campinas"
    assert data["geocoding"]["cells_count"] >= 1


def test_api_tool_cnpj_lookup_and_discover():
    res_cnpj = client.get("/api/tools/cnpj?cnpj=48.192.301/0001-10&import_as_lead=true&niche_slug=clinicas-odontologicas")
    assert res_cnpj.status_code == 200
    body = res_cnpj.json()
    assert body["cnpj_data"]["valid"] is True
    assert body["imported_lead"] is not None
    assert body["imported_lead"]["id"] > 0

    res_disc = client.post(
        "/api/tools/cnpj-discover",
        json={
            "city": "Campinas",
            "state": "SP",
            "niche_slugs": ["clinicas-odontologicas"],
            "days_opened": 90,
            "import_as_leads": True,
        },
    )
    assert res_disc.status_code == 200
    disc_body = res_disc.json()
    assert disc_body["discovery"]["total_found"] >= 2
    assert disc_body["imported_count"] >= 2


def test_api_tool_registro_br_site_health_and_xray():
    res_reg = client.get("/api/tools/registro-br?query=Clinica%20Odonto%20Inexistente%20999&city=Campinas")
    assert res_reg.status_code == 200
    reg_data = res_reg.json()
    assert reg_data["domain"].endswith(".com.br")
    assert len(reg_data["variations"]) == 3

    res_health = client.get("/api/tools/site-health?url=http://mastergroup-wix-demo.com.br")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["site_in_air"] is True
    assert health_data["resolved_ip"] == "185.230.63.107"

    res_xray = client.get("/api/tools/site-xray?url=http://mastergroup-wix-demo.com.br&company_name=Master%20Group&city=Campinas")
    assert res_xray.status_code == 200
    xray_data = res_xray.json()
    assert xray_data["detected_cms"] == "Wix"
    reports = xray_data["external_tools_links"]["embedded_reports"]
    assert reports["builtwith"]["server"] == "Wix Pepyaka Server"
    assert reports["whatcms"]["cms_name"] == "Wix"
    assert reports["wayback"]["wayback_days_since_update"] == 1450

    res_wb = client.get("/api/tools/wayback?url=http://mastergroup-wix-demo.com.br")
    assert res_wb.status_code == 200
    wb_data = res_wb.json()
    assert wb_data["total_snapshots"] == 4
    assert len(wb_data["snapshots_timeline"]) == 4
