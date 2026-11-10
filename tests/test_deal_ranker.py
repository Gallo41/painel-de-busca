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
    assert cents == 89000
    assert faixa == "R$ 600 a R$ 1.200"


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
        assert {"score_histogram", "funnel", "by_pain", "by_segment", "pipeline", "plan_days", "methodology"} <= set(data["analytics"])
        ranks = [x["rank"] for x in data["ranking"]]
        assert ranks == sorted(ranks)

        only = client.get("/api/leads/ranking?segment=odontologia&only_ready=true").json()
        assert [x["segment"]["slug"] for x in only["ranking"]] == ["odontologia"]
        assert only["ranking"][0]["price"]["alvo_cents"] > 0


# ---------------- preços reduzidos ----------------


def test_catalog_prices_were_lowered_and_ranker_follows():
    assert CATALOGO_SOLUCOES["LANDING_PAGE"]["faixa_preco"] == "R$ 600 a R$ 1.200"
    assert CATALOGO_SOLUCOES["SITE_INSTITUCIONAL"]["faixa_preco"] == "R$ 1.100 a R$ 2.000"
    assert CATALOGO_SOLUCOES["SISTEMA_SOB_MEDIDA"]["faixa_preco"] == "R$ 1.800 a R$ 3.800"
    top = suggest_price(_lead(review_count=900, title="Clínica Odonto Premium"))
    assert top["alvo_cents"] <= 199000  # nada acima do teto do site completo
    lp = suggest_price(_lead(review_count=3, title="Psicóloga Ana", niche_slug="psicologia-fisioterapia"))
    assert lp["scope_type"] == "LANDING_PAGE" and lp["alvo_cents"] <= 79000


# ---------------- analytics ----------------


def test_build_analytics_has_everything_the_dashboard_needs():
    from app.services.deal_ranker import build_analytics

    ranked = rank_leads(_batch())
    plan = build_outreach_plan(ranked, per_day=2)
    a = build_analytics(ranked, plan)

    assert sum(b["count"] for b in a["score_histogram"]) == len([r for r in ranked if r["close_chance"]["tier"] != "EXCLUIDO"])
    assert [b["from"] for b in a["score_histogram"]] == list(range(0, 100, 10))
    f = a["funnel"]
    assert [s["key"] for s in f] == ["total", "valid", "contact", "whatsapp", "ready", "tier_a"]
    counts = [s["count"] for s in f]
    assert counts == sorted(counts, reverse=True)
    assert f[0]["count"] == len(ranked)
    assert sum(p["count"] for p in a["by_pain"]) == len(ranked) - 1  # UNIMEP excluído não entra
    seg = {s["slug"]: s for s in a["by_segment"]}
    assert seg["odontologia"]["avg_price_cents"] > 0
    assert seg["odontologia"]["min_price_cents"] <= seg["odontologia"]["avg_price_cents"] <= seg["odontologia"]["max_price_cents"]
    assert {"ready_value_cents", "tier_a_value_cents"} <= set(a["pipeline"])
    assert [d["day"] for d in a["plan_days"]] == [p["day"] for p in plan]
    assert all({"A", "B", "C", "D"} <= set(d["tiers"]) for d in a["plan_days"])
    m = a["methodology"]
    assert sum(c["max_points"] for c in m["components"]) == 100
    assert [t["tier"] for t in m["tiers"]] == ["A", "B", "C", "D"]


def test_ready_report_ticket_follows_new_pricing():
    from app.routers.leads_router import _ensure_ready_report

    lead = _lead(review_count=3, title="Psicóloga Ana", niche_slug="psicologia-fisioterapia")
    lead["outreach_scripts"] = {"ready_report": {"ticket_range": "R$ 3.500 a R$ 8.000", "bullets": []}}
    out = _ensure_ready_report(lead)
    assert out["outreach_scripts"]["ready_report"]["ticket_range"] == suggest_price(lead)["faixa_text"]


# ---------------- preparo de fila (lote e semi-automático) ----------------


def test_prepare_queue_batch_enqueues_only_ready_and_respects_target(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.database import init_db, list_outreach_queue
    from app.services.outreach_generator import process_and_save_lead
    from app.services.deal_ranker import prepare_queue_batch
    from app.services.whatsapp_agent import OUTBOX_LOG

    db_file = str(tmp_path / "prep.db")
    monkeypatch.setenv("PAINEL_DB_PATH", db_file)
    init_db(db_path=db_file)
    OUTBOX_LOG.clear()

    saved_ids = []
    specs = [
        ("Dentista Top 1", "(19) 99111-0001", 120, "", None),
        ("Dentista Top 2", "(19) 99111-0002", 90, "", None),
        ("Dentista Tel Duplicado", "(19) 99111-0001", 110, "", "dup-phone-extra"),
        ("Clínica Só Fixo", "(19) 4102-8009", 150, "", None),
        ("UNIMEP Odonto", "(19) 99111-0003", 150, "http://unimep.edu.br", None),
        ("Dentista Top 3", "(19) 99111-0004", 30, "", None),
    ]
    for title, phone, reviews, site, place_id in specs:
        payload = {
            "title": title, "phone": phone, "website": site, "city": "Piracicaba", "state": "SP",
            "niche_slug": "clinicas-odontologicas", "review_count": reviews, "review_rating": 4.9,
        }
        if place_id:
            payload["place_id"] = place_id
        row = process_and_save_lead(
            payload,
            run_xray=True,
            skip_live_network=True,
            db_path=db_file,
        )
        saved_ids.append(row["id"])

    # Prepara lote de 2 primeiro
    res1 = prepare_queue_batch(day=1, per_day=2, only_missing_to_target=True, db_path=db_file)
    assert res1["enqueued_count"] == 2
    assert res1["ready_in_queue"] == 2
    assert len(OUTBOX_LOG) == 0  # nunca envia mensagem ao preparar!

    queue = list_outreach_queue(status="ready", db_path=db_file)
    assert len(queue) == 2
    assert {q["lead_id"] for q in queue} == {saved_ids[0], saved_ids[1]}
    assert queue[0]["diagnostic_context"]["ranking"]["tier"] == "A"

    # Chamar de novo com target=2 não adiciona duplicados
    res2 = prepare_queue_batch(day=1, per_day=2, only_missing_to_target=True, db_path=db_file)
    assert res2["enqueued_count"] == 0
    assert res2["already_full"] is True

    # Pular um item e completar até target=2: puxa o Top 3 (pula o duplicado, o fixo e a UNIMEP)
    from app.main import create_app

    with TestClient(create_app(db_path=db_file)) as client:
        skip_id = queue[0]["id"]
        assert client.patch(f"/api/outreach/{skip_id}/status", json={"status": "skipped"}).status_code == 200

        r_batch = client.post("/api/outreach/prepare-batch", json={"day": 1, "per_day": 2, "only_missing_to_target": True})
        assert r_batch.status_code == 200
        bdata = r_batch.json()
        assert bdata["enqueued_count"] == 1
        assert saved_ids[5] in bdata["lead_ids"]

        # Setting auto_prepare_queue persiste e import-csv auto-prepara novos leads
        r_set = client.put("/api/agent/settings", json={"auto_prepare_queue": True, "auto_prepare_batch_size": 5})
        assert r_set.status_code == 200
        assert r_set.json()["settings"]["auto_prepare_queue"] is True
        assert r_set.json()["settings"]["auto_prepare_batch_size"] == 5

        r_csv = client.post(
            "/api/leads/import-csv",
            json={
                "csv_text": "title,phone,review_count\nDra. Nova Silva,(19) 99888-7766,55\n",
                "city": "Piracicaba",
                "state": "SP",
                "niche_slug": "clinicas-odontologicas",
                "run_xray": False,
            },
        )
        assert r_csv.status_code == 200
        assert r_csv.json()["auto_prepared_queue_count"] == 1
        assert len(OUTBOX_LOG) == 0
