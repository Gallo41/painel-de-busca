import pytest
from app.services.business_discovery import (
    is_social_or_directory_url,
    suggest_domain_br,
    check_registro_br_availability,
    check_site_availability_and_ssl,
    build_casadosdados_links,
    lookup_cnpj_embedded,
    discover_companies_by_cnae_and_city,
)


def test_is_social_or_directory_url():
    assert is_social_or_directory_url("https://www.instagram.com/clinica_sorriso") is True
    assert is_social_or_directory_url("https://linktr.ee/advocaciasilva") is True
    assert is_social_or_directory_url("https://wa.me/5519999999999") is True
    assert is_social_or_directory_url("https://clinicasorriso.com.br") is False
    assert is_social_or_directory_url("") is False


def test_suggest_domain_br_strips_accents_and_stopwords():
    dom = suggest_domain_br("Clínica Odontológica Sorriso Prime LTDA - ME")
    assert dom.endswith(".com.br")
    assert "ltda" not in dom
    assert "ç" not in dom and "í" not in dom
    assert "sorrisoprime" in dom


def test_check_registro_br_availability_with_mock():
    # Mock opener function for deterministic testing
    def fake_fetcher(url: str):
        if "dominiolivre999" in url:
            return 404, b""
        return 200, b'{"handle": "clinica.com.br", "status": ["active"]}'

    res_free = check_registro_br_availability("dominiolivre999.com.br", http_get=fake_fetcher)
    assert res_free["available"] is True
    assert res_free["domain"] == "dominiolivre999.com.br"

    res_taken = check_registro_br_availability("clinica.com.br", http_get=fake_fetcher)
    assert res_taken["available"] is False


def test_check_site_availability_and_ssl_offline_domain():
    res = check_site_availability_and_ssl(
        "http://www.centralnegocios-offline-inexistente-999.com.br",
        timeout=1.5,
    )
    assert res["site_in_air"] is False
    assert "downforeveryoneorjustme.com" in res["downforeveryone_url"]


def test_build_casadosdados_links():
    links = build_casadosdados_links(
        city="Campinas",
        state="SP",
        niche_slugs=["clinicas-odontologicas"],
    )
    assert len(links) >= 1
    assert "8630-5/04" in links[0]["cnae_codes"]
    assert "Filtro Interno Ativo" in links[0]["instructions"]


def test_lookup_cnpj_embedded_and_discover():
    res = lookup_cnpj_embedded("48.192.301/0001-10", http_get=lambda u: (503, b""))
    assert res["valid"] is True
    assert res["cnpj_clean"] == "48192301000110"
    assert res["razao_social"] != ""
    assert len(res["qsa"]) >= 1

    disc = discover_companies_by_cnae_and_city("Campinas", "SP", ["clinicas-odontologicas"])
    assert disc["total_found"] >= 2
    assert disc["companies"][0]["city"] == "Campinas"
    assert disc["companies"][0]["suggested_domain"].endswith(".com.br")
