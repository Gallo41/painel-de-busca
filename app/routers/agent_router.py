from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.database import (
    get_agent_conversation,
    get_agent_settings,
    get_latest_lead_prototype,
    get_pending_price_consultation,
    list_agent_conversations,
    list_agent_messages,
    list_lead_prototypes,
    list_price_consultations,
    update_agent_settings,
)
from app.models import (
    AgentSettingsUpdate,
    AgentWebhookPayload,
    BossManualReplyRequest,
    ConversationControlRequest,
    PrototypeGenerateRequest,
    QueueConfirmSendRequest,
)
from app.services.ai_provider import get_ai_status
from app.services.prototype_generator import generate_prototype_for_lead
from app.services.whatsapp_agent import (
    OUTBOX_LOG,
    confirm_and_send_queue_item,
    get_bridge_status,
    handle_boss_incoming_message,
    pause_conversation,
    process_incoming_webhook,
    resume_conversation,
)

router = APIRouter(prefix="/api/agent", tags=["Agente WhatsApp, Preço & Protótipos IA"])


@router.get("/settings")
def api_get_agent_settings() -> Dict[str, Any]:
    settings = get_agent_settings()
    return {
        "settings": settings,
        "ai_status": get_ai_status(),
        "bridge": get_bridge_status(),
    }


@router.put("/settings")
def api_update_agent_settings(payload: AgentSettingsUpdate) -> Dict[str, Any]:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = update_agent_settings(updates)
    return {
        "ok": True,
        "settings": updated,
        "ai_status": get_ai_status(),
    }


@router.get("/bridge/status")
def api_get_bridge_status() -> Dict[str, Any]:
    return get_bridge_status()


@router.post("/queue/{queue_id}/confirm-send")
def api_agent_confirm_queue_send(
    queue_id: int,
    payload: Optional[QueueConfirmSendRequest] = None,
) -> Dict[str, Any]:
    try:
        custom_msg = payload.custom_message if payload else None
        return confirm_and_send_queue_item(queue_id=queue_id, custom_message=custom_msg)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/webhook")
def api_agent_webhook(
    payload: Dict[str, Any],
    immediate: bool = Query(False, description="Executa sem debounce (útil para simulador e testes)"),
) -> Dict[str, Any]:
    return process_incoming_webhook(payload=payload, immediate=immediate)


@router.get("/conversations")
def api_list_conversations(limit: int = Query(50, ge=1, le=200)) -> List[Dict[str, Any]]:
    convs = list_agent_conversations(limit=limit)
    for c in convs:
        proto = get_latest_lead_prototype(int(c["lead_id"]))
        c["has_prototype"] = proto is not None
        c["prototype_preview_url"] = f"/api/agent/prototypes/{c['lead_id']}/preview" if proto else None
    return convs


@router.get("/conversations/{conversation_id}")
def api_get_conversation_detail(conversation_id: int) -> Dict[str, Any]:
    conv = get_agent_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    messages = list_agent_messages(conversation_id, limit=200)
    proto = get_latest_lead_prototype(int(conv["lead_id"]))
    return {
        "conversation": conv,
        "messages": messages,
        "prototype": proto,
    }


@router.post("/conversations/{conversation_id}/pause")
def api_pause_conversation(
    conversation_id: int,
    payload: Optional[ConversationControlRequest] = None,
) -> Dict[str, Any]:
    settings = get_agent_settings()
    mins = (
        payload.pause_minutes
        if payload and payload.pause_minutes is not None
        else int(settings.get("pause_minutes_on_human") or 60)
    )
    reason = (payload.reason if payload and payload.reason else "pausado_pelo_painel")
    updated = pause_conversation(conversation_id=conversation_id, minutes=mins, reason=reason)
    if not updated:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return {"ok": True, "conversation": updated}


@router.post("/conversations/{conversation_id}/resume")
def api_resume_conversation(conversation_id: int) -> Dict[str, Any]:
    updated = resume_conversation(conversation_id=conversation_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return {"ok": True, "conversation": updated}


@router.get("/price-consultations")
def api_list_price_consultations(limit: int = Query(30, ge=1, le=100)) -> List[Dict[str, Any]]:
    return list_price_consultations(limit=limit)


@router.post("/price-consultations/{consultation_id}/approve")
def api_approve_price_consultation(
    consultation_id: int,
    payload: BossManualReplyRequest,
) -> Dict[str, Any]:
    pending = get_pending_price_consultation(consultation_id=consultation_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Consulta de preço não encontrada")
    settings = get_agent_settings()
    boss_phone = settings.get("boss_phone") or "551999958516"
    text_with_id = f"#{consultation_id} {payload.reply_text.strip()}"
    return handle_boss_incoming_message(boss_chatid=boss_phone, text=text_with_id)


@router.post("/leads/{lead_id}/generate-prototype")
def api_generate_lead_prototype(
    lead_id: int,
    payload: Optional[PrototypeGenerateRequest] = None,
) -> Dict[str, Any]:
    try:
        custom_inst = payload.custom_instructions if payload else None
        scope_ov = payload.scope_override if payload else None
        proto = generate_prototype_for_lead(
            lead_id=lead_id,
            custom_instructions=custom_inst,
            scope_override=scope_ov,
            notify_boss=True,
        )
        return {"ok": True, "prototype": proto}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prototypes")
def api_list_prototypes(limit: int = Query(30, ge=1, le=100)) -> List[Dict[str, Any]]:
    items = list_lead_prototypes(limit=limit)
    for it in items:
        it["preview_url"] = f"/api/agent/prototypes/{it['lead_id']}/preview"
    return items


@router.get("/prototypes/{lead_id}/preview", response_class=HTMLResponse)
def api_preview_lead_prototype(lead_id: int) -> HTMLResponse:
    proto = get_latest_lead_prototype(lead_id)
    if not proto or not proto.get("html_content"):
        raise HTTPException(status_code=404, detail="Protótipo ainda não gerado para este lead.")
    return HTMLResponse(content=proto["html_content"])


@router.get("/outbox")
def api_get_outbox_log(limit: int = Query(50, ge=1, le=200)) -> List[Dict[str, Any]]:
    return list(reversed(OUTBOX_LOG[-limit:]))
