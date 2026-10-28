import pytest
from app.services.site_xray import (
    detect_cms_and_tech_stack,
    check_wayback_machine,
    build_external_xray_links,
    run_full_xray_for_lead,
)


def test_detect_cms_wordpress_and_widgets():
    html = """
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="generator" content="WordPress 6.4">
        <link rel="stylesheet" href="/wp-content/themes/astra/style.css">
        <script src="https://www.googletagmanager.com/gtag/js?id=G-123"></script>
      </head>
      <body>
        <a href="https://wa.me/5519999999999">Chamar no WhatsApp</a>
      </body>
    </html>
    """
    res = detect_cms_and_tech_stack(html, headers={"server": "nginx"}, url="https://clinica.com.br")
    assert res["detected_cms"] == "WordPress"
    assert "WordPress" in res["tech_stack"]
    assert "Google Analytics / GTM" in res["tech_stack"]
    assert res["has_whatsapp_widget"] is True
    assert res["has_analytics_pixel"] is True
    assert res["is_mobile_friendly"] is True


def test_detect_cms_wix():
    html = "<script src='https://static.parastorage.com/services/wix-bolt/bolt.js'></script>"
    res = detect_cms_and_tech_stack(html, headers={"x-wix-request-id": "123"}, url="http://site.com.br")
    assert res["detected_cms"] == "Wix"
    assert res["is_mobile_friendly"] is False


def test_check_wayback_machine_with_mock():
    def fake_get(url: str):
        return (
            200,
            b'{"archived_snapshots": {"closest": {"available": true, "timestamp": "20210510120000", "url": "http://web.archive.org/web/20210510/http://site.com.br"}}}',
        )

    wb = check_wayback_machine("https://site.com.br", http_get=fake_get)
    assert wb["wayback_last_seen"] == "2021-05-10"
    assert wb["wayback_days_since_update"] > 1000
    assert "web.archive.org" in wb["wayback_url"]


def test_build_external_xray_links_has_all_8_tools():
    links = build_external_xray_links(
        website="https://clinicasorriso.com.br",
        suggested_domain="clinicasorriso.com.br",
        company_name="Clínica Sorriso",
        city="Campinas",
    )
    for key in (
        "google_maps",
        "casadosdados",
        "registro_br",
        "downforeveryone",
        "builtwith",
        "wappalyzer",
        "whatcms",
        "web_archive",
    ):
        assert key in links
        assert links[key].startswith("https://")


def test_run_full_xray_for_lead_without_website():
    lead = {
        "title": "Odonto Prime Campinas",
        "website": "",
        "city": "Campinas",
    }
    xray = run_full_xray_for_lead(lead, skip_live_network=True)
    assert xray["has_website"] is False
    assert xray["suggested_domain"].endswith(".com.br")
    assert xray["detected_cms"] == "Sem Site"
    assert "builtwith" in xray["external_tools_links"]
