import pytest
from app.services.business_discovery import (
    is_social_or_directory_url,
    suggest_domain_br,
    check_registro_br_availability,
    check_site_availability_and_ssl,
    build_casadosdados_links,
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
    assert "casadosdados.com.br" in links[0]["search_url"]
