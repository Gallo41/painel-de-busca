import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def agent_client(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_agent.db")
    monkeypatch.setenv("PAINEL_DB_PATH", db_file)
    monkeypatch.setenv("PAINEL_AI_OFFLINE", "1")

    from app.main import create_app
    from app.services.whatsapp_agent import OUTBOX_LOG

    OUTBOX_LOG.clear()
    app = create_app(db_path=db_file)
    with TestClient(app) as client:
        yield client


def _create_sample_lead(client: TestClient) -> int:
    r = client.post(
        "/api/leads",
        json={
            "title": "Barbearia Dom Pedro",
            "category": "Barbearia",
            "phone": "(19) 98877-6655",
            "city": "Piracicaba",
            "state": "SP",
            "niche_slug": "barbearia",
            "review_rating": 4.9,
            "review_count": 84,
            "run_xray": False,
        },
    )
    assert r.status_code == 200
    return int(r.json()["id"])


def test_agent_default_settings_and_ai_keys(agent_client: TestClient):
    res = agent_client.get("/api/agent/settings")
    assert res.status_code == 200
    data = res.json()
    st = data["settings"]
    assert st["test_mode"] is True
    assert st["boss_phone"] == "551999958516"
    assert st["test_client_phone"] == "5519996109028"
    assert data["ai_status"]["ready"] is True


def test_queue_confirmation_redirects_to_test_number_and_authorizes_negotiation(agent_client: TestClient):
    lead_id = _create_sample_lead(agent_client)

    # 1. Enfileira o lead selecionado
    r_enq = agent_client.post(
        "/api/outreach/enqueue",
        json={"lead_ids": [lead_id], "channels": ["whatsapp"]},
    )
    assert r_enq.status_code == 200
    queue_id = r_enq.json()["queue_ids"][0]

    # 2. Confirma na fila -> deve enviar 1ª mensagem para o número de teste (+55 19 99610-9028)
    r_conf = agent_client.post(f"/api/outreach/{queue_id}/confirm-send", json={})
    assert r_conf.status_code == 200
    conf_data = r_conf.json()
    assert conf_data["ok"] is True
    assert conf_data["is_test_mode"] is True
    assert conf_data["target_chatid"] == "5519996109028"
    assert conf_data["queue_item"]["status"] == "sent"
    conv_id = conf_data["conversation"]["id"]

    # 3. Cliente de teste responde -> Agente negocia vendendo o resultado da LP
    r_turn = agent_client.post(
        "/api/agent/webhook?immediate=true",
        json={
            "EventType": "messages",
            "message": {
                "fromMe": False,
                "isGroup": False,
                "type": "text",
                "chatid": "5519996109028@s.whatsapp.net",
                "text": "Já tenho Instagram, por que eu precisaria de uma página?",
                "senderName": "Pedro",
            },
        },
    )
    assert r_turn.status_code == 200
    turn_data = r_turn.json()
    assert turn_data["ok"] is True
    assert turn_data["conversation_id"] == conv_id
    assert "whatsapp" in turn_data["reply"].lower() or "google" in turn_data["reply"].lower()


def test_fiscal_scope_is_strictly_refused(agent_client: TestClient):
    lead_id = _create_sample_lead(agent_client)
    queue_id = agent_client.post(
        "/api/outreach/enqueue", json={"lead_ids": [lead_id], "channels": ["whatsapp"]}
    ).json()["queue_ids"][0]
    agent_client.post(f"/api/outreach/{queue_id}/confirm-send", json={})

    # Cliente pede sistema com agendamento + emissão de Nota Fiscal (NF-e / cupom fiscal)
    r_fiscal = agent_client.post(
        "/api/agent/webhook?immediate=true",
        json={
            "EventType": "messages",
            "message": {
                "fromMe": False,
                "isGroup": False,
                "type": "text",
                "chatid": "5519996109028@s.whatsapp.net",
                "text": "Vocês fazem um sistema de agendamento que também emita nota fiscal NF-e e calcule imposto?",
            },
        },
    )
    assert r_fiscal.status_code == 200
    data = r_fiscal.json()
    assert data["ok"] is True
    assert data["action"] == "fiscal_guardrail"
    reply_lower = data["reply"].lower()
    assert "não fazemos" in reply_lower or "nao fazemos" in reply_lower
    assert "tribut" in reply_lower or "fiscal" in reply_lower


def test_price_consultation_with_boss_551999958516_and_forwarding(agent_client: TestClient):
    lead_id = _create_sample_lead(agent_client)
    queue_id = agent_client.post(
        "/api/outreach/enqueue", json={"lead_ids": [lead_id], "channels": ["whatsapp"]}
    ).json()["queue_ids"][0]
    agent_client.post(f"/api/outreach/{queue_id}/confirm-send", json={})

    # 1. Cliente pergunta quanto custa
    r_price = agent_client.post(
        "/api/agent/webhook?immediate=true",
        json={
            "EventType": "messages",
            "message": {
                "fromMe": False,
                "isGroup": False,
                "type": "text",
                "chatid": "5519996109028@s.whatsapp.net",
                "text": "Gostei da ideia da Landing Page com catálogo. Quanto custa pra fazer?",
            },
        },
    )
    assert r_price.status_code == 200
    pdata = r_price.json()
    assert pdata["ok"] is True
    assert pdata["action"] == "price_consulted_boss"
    assert "R$" in pdata["reply"]
    consultation = pdata["price_consultation"]
    assert consultation is not None
    cid = consultation["id"]

    # Verifica que o WhatsApp do Chefe (+551999958516) recebeu a consulta no OUTBOX
    outbox = agent_client.get("/api/agent/outbox").json()
    boss_msgs = [m for m in outbox if m["number"] == "551999958516" and f"#{cid}" in m["text"]]
    assert len(boss_msgs) >= 1

    # 2. Chefe (+551999958516) responde aprovando o preço pelo WhatsApp
    r_boss = agent_client.post(
        "/api/agent/webhook?immediate=true",
        json={
            "EventType": "messages",
            "message": {
                "fromMe": False,
                "isGroup": False,
                "type": "text",
                "chatid": "551999958516@s.whatsapp.net",
                "text": f"#{cid} pode fazer R$ 1.290 em 3x sem juros",
            },
        },
    )
    assert r_boss.status_code == 200
    bdata = r_boss.json()
    assert bdata["ok"] is True
    assert bdata["from_boss"] is True
    assert bdata["action"] == "price_forwarded_to_client"
    assert "R$ 1.290 em 3x sem juros" in bdata["client_message"]


def test_human_handoff_pauses_agent_automatically(agent_client: TestClient):
    lead_id = _create_sample_lead(agent_client)
    queue_id = agent_client.post(
        "/api/outreach/enqueue", json={"lead_ids": [lead_id], "channels": ["whatsapp"]}
    ).json()["queue_ids"][0]
    conf = agent_client.post(f"/api/outreach/{queue_id}/confirm-send", json={}).json()
    conv_id = conf["conversation"]["id"]

    # 1. Humano digita manualmente no aparelho (fromMe=True, wasSentByApi=False)
    r_handoff = agent_client.post(
        "/api/agent/webhook?immediate=true",
        json={
            "EventType": "messages",
            "message": {
                "fromMe": True,
                "wasSentByApi": False,
                "isGroup": False,
                "type": "text",
                "chatid": "5519996109028@s.whatsapp.net",
                "text": "Oi Pedro, aqui é o dono, vou fechar direto com você!",
            },
        },
    )
    assert r_handoff.status_code == 200
    assert r_handoff.json()["handoff"] is True

    # 2. Cliente manda nova mensagem -> Agente deve ficar em silêncio (ignorado)
    r_ignored = agent_client.post(
        "/api/agent/webhook?immediate=true",
        json={
            "EventType": "messages",
            "message": {
                "fromMe": False,
                "isGroup": False,
                "type": "text",
                "chatid": "5519996109028@s.whatsapp.net",
                "text": "Combinado, me passa o PIX!",
            },
        },
    )
    assert r_ignored.status_code == 200
    assert r_ignored.json()["ignored"] is True
    assert r_ignored.json()["reason"] == "conversation_paused_by_human"

    # 3. Retoma conversa pelo Painel -> volta a responder
    r_res = agent_client.post(f"/api/agent/conversations/{conv_id}/resume")
    assert r_res.status_code == 200
    assert r_res.json()["conversation"]["status"] == "active"


def test_close_deal_triggers_ai_prototype_and_notifies_boss(agent_client: TestClient):
    lead_id = _create_sample_lead(agent_client)
    queue_id = agent_client.post(
        "/api/outreach/enqueue", json={"lead_ids": [lead_id], "channels": ["whatsapp"]}
    ).json()["queue_ids"][0]
    agent_client.post(f"/api/outreach/{queue_id}/confirm-send", json={})

    # Cliente fecha negócio na conversa
    r_close = agent_client.post(
        "/api/agent/webhook?immediate=true",
        json={
            "EventType": "messages",
            "message": {
                "fromMe": False,
                "isGroup": False,
                "type": "text",
                "chatid": "5519996109028@s.whatsapp.net",
                "text": "Fechado! Pode montar o protótipo com agendamento e catálogo de cortes.",
            },
        },
    )
    assert r_close.status_code == 200
    cdata = r_close.json()
    assert cdata["ok"] is True
    assert cdata["action"] == "deal_closed_prototype_generated"
    assert cdata["prototype"] is not None

    # Verifica se o preview HTML do protótipo está acessível no Painel
    r_prev = agent_client.get(f"/api/agent/prototypes/{lead_id}/preview")
    assert r_prev.status_code == 200
    assert "Barbearia Dom Pedro" in r_prev.text
    assert "<!DOCTYPE html>" in r_prev.text

    # Verifica que o Chefe (+551999958516) recebeu aviso de protótipo pronto
    outbox = agent_client.get("/api/agent/outbox").json()
    proto_boss_msgs = [m for m in outbox if m["number"] == "551999958516" and "Protótipo IA Pronto" in m["text"]]
    assert len(proto_boss_msgs) >= 1
