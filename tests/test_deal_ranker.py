from app.services.deal_ranker import (
    build_outreach_plan,
    detect_segment,
    group_by_segment,
    rank_leads,
    score_close_chance,
    suggest_price,
)
from app.services.whatsapp_agent import CATALOGO_SOLUCOES, calculate_suggested_price


def _lead(**kw):
    base = {
        "id": 1,
        "title": "Clínica Exemplo",
        "niche_slug": "clinicas-odontologicas",
        "category": "",
        "phone": "(19)99999-1111",
        "whatsapp_clean": "5519999991111",
        "emails": "",
        "instagram": "",
        "website": "",
        "review_count": 40,
        "review_rating": 4.8,
        "primary_pain": "SEM_SITE",
        "recommended_service": "SITE_NOVO",
        "opportunity_score": 98,
        "domain_available_br": 1,
        "lead_status": "novo",
        "city": "Piracicaba",
    }
    base.update(kw)
    return base


# ---------------- segmento real ----------------


def test_segment_overrides_wrong_niche_slug():
    lead = _lead(title="Psicóloga Camila Frassetto", niche_slug="academias-studios-pilates")
    assert detect_segment(lead)["slug"] == "psicologia"


def test_segment_construtora_is_not_imobiliaria():
    lead = _lead(title="Le Mans Construtora", niche_slug="imobiliarias-corretores")
    assert detect_segment(lead)["slug"] == "construtoras"


def test_segment_uses_category_and_falls_back_to_niche_slug():
    assert detect_segment(_lead(title="Sorriso Mais", category="Dentista"))["slug"] == "odontologia"
    fallback = detect_segment(_lead(title="Xyz", category="", niche_slug="escritorios-advocacia"))
    assert fallback["slug"] == "advocacia"


def test_segment_uses_social_handle_and_never_calls_a_doctor_a_gym():
    by_handle = _lead(title="Valdenice Freitas", niche_slug="academias-studios-pilates",
                      instagram="https://instagram.com/valfreitaspsi?igshid=1")
    assert detect_segment(by_handle)["slug"] == "psicologia"
    doctor = _lead(title="Dra. Ana Beatriz Volpato", niche_slug="academias-studios-pilates")
    assert detect_segment(doctor)["slug"] == "saude"
    gym = _lead(title="Monster Fitness", niche_slug="academias-studios-pilates")
    assert detect_segment(gym)["slug"] == "academias"


def test_price_is_not_pinned_at_the_catalog_ceiling():
    p = suggest_price(_lead(review_count=150, title="Clínica Odontológica Sorriso"))
    assert p["alvo_cents"] < p["faixa_max_cents"] - 10000  # R$ 100 de folga
    assert p["alvo_cents"] > p["piso_cents"]


# ---------------- chance de fechar ----------------


def test_mobile_whatsapp_beats_landline():
    mobile = score_close_chance(_lead())
    landline = score_close_chance(_lead(phone="(19)4102-8009", whatsapp_clean="551941028009"))
    assert mobile["score"] > landline["score"]
    assert mobile["channel"] == "whatsapp"
    assert landline["channel"] == "telefone"


def test_strong_pain_and_social_proof_rank_higher():
    hot = score_close_chance(_lead(primary_pain="SITE_FORA_DO_AR", review_count=120))
    cold = score_close_chance(_lead(primary_pain="OPORTUNIDADE_SISTEMA", review_count=2, website="http://x.com"))
    assert hot["score"] > cold["score"] + 20


def test_institutions_and_discarded_leads_are_excluded():
    uni = score_close_chance(_lead(title="Clínica de Fisioterapia UNIMEP", website="http://unimep.edu.br/f"))
    gov = score_close_chance(_lead(title="Posto de saúde", website="http://www.piracicaba.sp.gov.br/x"))
    dropped = score_close_chance(_lead(lead_status="nao_fazer"))
    for r in (uni, gov, dropped):
        assert r["tier"] == "EXCLUIDO"
        assert r["score"] == 0


def test_simulated_demo_leads_are_excluded():
    fake = score_close_chance(_lead(source="cnae_recem_abertas"))
    fake2 = score_close_chance(_lead(place_id="sim_123"))
    for r in (fake, fake2):
        assert r["tier"] == "EXCLUIDO" and "LEAD_SIMULADO" in r["flags"]


def test_score_is_bounded_and_has_explained_factors():
    r = score_close_chance(_lead(primary_pain="SITE_FORA_DO_AR", review_count=900, instagram="http://insta/x"))
    assert 0 <= r["score"] <= 100
    assert r["factors"] and all("label" in f and "points" in f for f in r["factors"])
    assert r["tier"] in {"A", "B", "C", "D"}


# ---------------- preço ----------------


def test_price_stays_inside_official_catalog_band():
    for lead in (
        _lead(review_count=0),
        _lead(review_count=900),
        _lead(primary_pain="OPORTUNIDADE_SISTEMA", recommended_service="SISTEMA_COMPLEXO", review_count=300),
    ):
        p = suggest_price(lead)
        sol = CATALOGO_SOLUCOES[p["scope_type"]]
        assert p["piso_cents"] < p["alvo_cents"] < p["faixa_max_cents"]
        assert p["faixa_min_cents"] <= p["alvo_cents"]
        assert p["alvo_cents"] % 1000 == 0  # sempre em reais múltiplos de 10
        assert sol["faixa_preco"]  # escopo existe no catálogo
        assert p["faixa_text"].startswith("R$ ") and " a R$ " in p["faixa_text"]


def test_bigger_and_high_ticket_niches_cost_more():
    small = suggest_price(_lead(review_count=3, niche_slug="psicologia-fisioterapia", title="Psicóloga Ana"))
    big = suggest_price(_lead(review_count=300, title="Clínica Odonto Premium"))
    assert big["alvo_cents"] > small["alvo_cents"]


def test_system_scope_only_for_real_size_or_complex_need():
    tiny = suggest_price(
        _lead(primary_pain="OPORTUNIDADE_SISTEMA", recommended_service="SISTEMA_COMPLEXO", review_count=4, website="http://a.com")
    )
    assert tiny["scope_type"] != "SISTEMA_SOB_MEDIDA"
    large = suggest_price(
        _lead(primary_pain="OPORTUNIDADE_SISTEMA", recommended_service="SISTEMA_COMPLEXO", review_count=200, website="http://a.com")
    )
    assert large["scope_type"] == "SISTEMA_SOB_MEDIDA"


def test_explicit_scope_is_respected():
    p = suggest_price(_lead(), scope_type="SITE_INSTITUCIONAL")
    assert p["scope_type"] == "SITE_INSTITUCIONAL"


# ---------------- ranking, grupos e plano ----------------


def _batch():
    return [
        _lead(id=1, title="Dra. Ana", review_count=60),
        _lead(id=2, title="Clínica Fone", phone="(19)4102-8009", whatsapp_clean="551941028009", review_count=60),
        _lead(id=3, title="Le Mans Construtora", niche_slug="imobiliarias-corretores", primary_pain="OPORTUNIDADE_SISTEMA",
              recommended_service="SISTEMA_COMPLEXO", website="http://l.com", review_count=140),
        _lead(id=4, title="UNIMEP Fisio", website="http://unimep.edu.br"),
        _lead(id=5, title="Dr. Duplicado", whatsapp_clean="5519999991111", phone="(19)99999-1111", review_count=5),
    ]


def test_rank_leads_orders_desc_and_flags_duplicate_phone():
    ranked = rank_leads(_batch())
    scores = [r["close_chance"]["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
    assert [r["rank"] for r in ranked] == list(range(1, len(ranked) + 1))
    # excluídos vão pro fim
    assert ranked[-1]["close_chance"]["tier"] == "EXCLUIDO"
    # telefone repetido: o de menor score é marcado como duplicado e não pode ser disparado duas vezes
    dup = [r for r in ranked if "TELEFONE_DUPLICADO" in r["close_chance"]["flags"]]
    assert len(dup) >= 1
    assert all(r["outreach_ready"] is False for r in dup)


def test_group_by_segment_orders_segments_by_best_potential():
    groups = group_by_segment(rank_leads(_batch()))
    assert groups, "deve haver grupos"
    first_scores = [g["leads"][0]["close_chance"]["score"] for g in groups]
    assert first_scores == sorted(first_scores, reverse=True)
    for g in groups:
        s = [x["close_chance"]["score"] for x in g["leads"]]
        assert s == sorted(s, reverse=True)
        assert {"slug", "label", "total", "avg_score", "tier_a"} <= set(g)


def test_outreach_plan_respects_daily_limit_and_skips_unreachable():
    leads = [_lead(id=i, title=f"Dr. {i}", whatsapp_clean=f"55199999{i:05d}", phone="(19)99999-0000") for i in range(1, 31)]
    leads.append(_lead(id=99, title="Sem zap", phone="", whatsapp_clean="", emails="", instagram=""))
    plan = build_outreach_plan(rank_leads(leads), per_day=12)
    assert [len(d["leads"]) for d in plan] == [12, 12, 6]
    assert all(l["lead"]["id"] != 99 for d in plan for l in d["leads"])
    assert plan[0]["day"] == 1


# ---------------- integração com o agente ----------------


def test_agent_price_uses_lead_specific_value_when_lead_given():
    lead = _lead(review_count=300, title="Clínica Odonto Premium")
    cents, faixa, sol = calculate_suggested_price("LANDING_PAGE", "quanto custa?", lead=lead)
    expected = suggest_price(lead, scope_type="LANDING_PAGE")
    assert cents == expected["alvo_cents"]
    assert faixa == expected["faixa_text"]
    assert sol["codigo"] == "LANDING_PAGE"


def test_agent_price_without_lead_keeps_legacy_behavior():
    cents, faixa, _ = calculate_suggested_price("LANDING_PAGE", "quanto custa?")
    assert cents == 139000
    assert faixa == "R$ 900 a R$ 1.800"


# ---------------- API ----------------


def test_ranking_endpoint_groups_by_real_segment_and_filters(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    db_file = str(tmp_path / "rank.db")
    monkeypatch.setenv("PAINEL_DB_PATH", db_file)
    from app.main import create_app

    with TestClient(create_app(db_path=db_file)) as client:
        for title, phone, reviews in [
            ("Psicóloga Camila Frassetto", "(19) 99111-2222", 30),
            ("Sorriso Odonto", "(19) 99333-4444", 80),
            ("Clínica Fixo", "(19) 4102-8009", 80),
        ]:
            r = client.post("/api/leads", json={
                "title": title, "phone": phone, "city": "Piracicaba", "state": "SP",
                "niche_slug": "academias-studios-pilates", "review_count": reviews, "run_xray": False,
            })
            assert r.status_code == 200

        res = client.get("/api/leads/ranking?per_day=1")
        assert res.status_code == 200
        data = res.json()
        slugs = {g["slug"] for g in data["groups"]}
        assert {"psicologia", "odontologia"} <= slugs
        assert data["summary"]["total"] == 3
        assert data["summary"]["ready"] == 2  # o fixo não conta como WhatsApp
        assert len(data["plan"]) == 2
        ranks = [x["rank"] for x in data["ranking"]]
        assert ranks == sorted(ranks)

        only = client.get("/api/leads/ranking?segment=odontologia&only_ready=true").json()
        assert [x["segment"]["slug"] for x in only["ranking"]] == ["odontologia"]
        assert only["ranking"][0]["price"]["alvo_cents"] > 0
