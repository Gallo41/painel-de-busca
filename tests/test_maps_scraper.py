import pytest
from app.services.niches_catalog import DEFAULT_NICHES, get_niches_by_slugs
from app.services.maps_scraper import (
    normalize_whatsapp_br,
    build_keywords_for_job,
    parse_csv_content_to_leads,
    generate_sample_leads_for_niches,
)


def test_default_niches_catalog_completeness():
    assert len(DEFAULT_NICHES) >= 10
    slugs = {n["slug"] for n in DEFAULT_NICHES}
    assert "clinicas-odontologicas" in slugs
    assert "escritorios-advocacia" in slugs
    assert "imobiliarias-corretores" in slugs
    assert "oficinas-estetica-automotiva" in slugs

    selected = get_niches_by_slugs(["clinicas-odontologicas", "escritorios-advocacia"])
    assert len(selected) == 2


def test_normalize_whatsapp_br():
    assert normalize_whatsapp_br("(19) 99876-5432") == "5519998765432"
    assert normalize_whatsapp_br("+55 11 98765-4321") == "5511987654321"
    assert normalize_whatsapp_br("019 3232-4455") == "551932324455"
    assert normalize_whatsapp_br("") == ""
    assert normalize_whatsapp_br("123") == ""


def test_build_keywords_for_job():
    kws = build_keywords_for_job(
        city="Campinas",
        state="SP",
        niche_slugs=["clinicas-odontologicas"],
        custom_keywords=["implante dentário"],
    )
    assert any("Campinas SP" in k for k in kws)
    assert "implante dentário em Campinas SP" in kws


def test_parse_csv_content_to_leads():
    csv_text = (
        "title,phone,emails,website,category,address,review_rating,review_count,instagram\n"
        "Clínica Sorriso,(19) 99111-2222,contato@sorriso.com.br,https://sorriso.com.br,Dentista,Rua A 10,4.8,64,https://instagram.com/sorriso\n"
        "Oficina do João,(19) 98888-7777,,,Mecânica,Rua B 20,4.6,42,\n"
    )
    leads = parse_csv_content_to_leads(csv_text, city="Campinas", state="SP", niche_slug="clinicas-odontologicas")
    assert len(leads) == 2
    assert leads[0]["title"] == "Clínica Sorriso"
    assert leads[0]["whatsapp_clean"] == "5519991112222"
    assert leads[1]["website"] == ""
    assert leads[1]["whatsapp_clean"] == "5519988887777"


def test_generate_sample_leads_for_niches():
    leads = generate_sample_leads_for_niches(
        city="Campinas",
        state="SP",
        niche_slugs=["clinicas-odontologicas", "imobiliarias-corretores"],
    )
    assert len(leads) >= 6
    # Deve conter variedade de cenarios (sem site, só rede social, site fora do ar, oportunidade de sistema)
    websites = [l.get("website", "") for l in leads]
    assert any(w == "" for w in websites)
    assert any("instagram.com" in w or "linktr.ee" in w for w in websites)
