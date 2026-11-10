import csv
import io
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.database import (
    claim_next_outreach,
    enqueue_outreach,
    get_lead,
    list_leads,
    list_outreach_queue,
    update_outreach_status,
)
from app.models import (
    OutreachClaimRequest,
    OutreachEnqueueRequest,
    OutreachStatusUpdate,
    QueueConfirmSendRequest,
)
from app.services.whatsapp_agent import confirm_and_send_queue_item

router = APIRouter(prefix="/api/outreach", tags=["Outreach & Automação Futura"])


@router.post("/enqueue")
def api_enqueue_outreach(payload: OutreachEnqueueRequest) -> Dict[str, Any]:
    """
    Adiciona leads selecionados na fila de disparo (`outreach_queue`), já com os scripts
    personalizados pelo Raio-X e o contexto diagnóstico completo para consumo por bots futuros.
    """
    queue_ids: List[int] = []
    for lid in payload.lead_ids:
        lead = get_lead(lid)
        if not lead:
            continue
        scripts = lead.get("outreach_scripts") or {}
        diag_ctx = scripts.get("automation_payload") or {
            "primary_pain": lead.get("primary_pain"),
            "recommended_service": lead.get("recommended_service"),
            "opportunity_score": lead.get("opportunity_score"),
            "suggested_domain": lead.get("suggested_domain"),
        }

        for ch in payload.channels:
            ch_clean = ch.strip().lower()
            if ch_clean == "whatsapp":
                recipient = lead.get("whatsapp_clean") or lead.get("phone") or ""
                subject = ""
                body = scripts.get("whatsapp") or ""
            elif ch_clean == "email":
                recipient = (lead.get("emails") or "").split(",")[0].strip()
                subject = scripts.get("email_subject") or f"Diagnóstico Digital - {lead.get('title')}"
                body = scripts.get("email_body") or scripts.get("whatsapp") or ""
            elif ch_clean == "instagram":
                recipient = lead.get("instagram") or ""
                subject = ""
                body = scripts.get("instagram_dm") or ""
            else:
                continue

            qid = enqueue_outreach(
                lead_id=lid,
                channel=ch_clean,
                recipient=recipient,
                subject=subject,
                message_body=body,
                diagnostic_context=diag_ctx,
                scheduled_for=payload.scheduled_for,
            )
            queue_ids.append(qid)

    return {"enqueued_count": len(queue_ids), "queue_ids": queue_ids}


@router.get("/queue")
def api_list_outreach_queue(
    status: Optional[str] = Query(None, description="'ready', 'sending', 'sent', 'replied', 'failed'"),
    channel: Optional[str] = Query(None, description="'whatsapp', 'email', 'instagram'"),
    limit: int = Query(100, ge=1, le=500),
) -> List[Dict[str, Any]]:
    return list_outreach_queue(status=status, channel=channel, limit=limit)


@router.post("/claim")
def api_claim_next_outreach(payload: OutreachClaimRequest) -> Dict[str, Any]:
    """
    Endpoint para o futuro robô de automação (Evolution API / WPPConnect / n8n / Worker Python)
    reservar atomicamente o próximo contato da fila `ready`.
    """
    item = claim_next_outreach(channel=payload.channel, worker_id=payload.worker_id)
    return {"has_next": item is not None, "item": item}


@router.patch("/{queue_id}/status")
def api_update_outreach_item_status(queue_id: int, payload: OutreachStatusUpdate) -> Dict[str, Any]:
    """
    Webhook / Callback para atualizar o status do disparo (`sent`, `replied`, `failed`)
    e sincronizar automaticamente o status do lead no funil de vendas.
    """
    updated = update_outreach_status(
        queue_id=queue_id,
        status=payload.status,
        external_message_id=payload.external_message_id,
        webhook_response=payload.webhook_response,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Item da fila de outreach não encontrado")
    return updated


@router.post("/{queue_id}/confirm-send")
def api_confirm_and_send_outreach_item(
    queue_id: int,
    payload: Optional[QueueConfirmSendRequest] = None,
) -> Dict[str, Any]:
    """
    Confirma um item da fila, dispara a 1ª mensagem no WhatsApp (respeitando o Modo Teste para +55 19 99610-9028
    ou enviando ao cliente real se aprovado para Produção) e autoriza o Agente a iniciar a negociação.
    """
    try:
        custom_msg = payload.custom_message if payload else None
        return confirm_and_send_queue_item(queue_id=queue_id, custom_message=custom_msg)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/confirm-send-all")
def api_confirm_and_send_all_ready() -> Dict[str, Any]:
    """Confirma e dispara a 1ª mensagem para todos os itens com status `ready` na fila."""
    ready_items = list_outreach_queue(status="ready", channel="whatsapp", limit=100)
    results = []
    for it in ready_items:
        try:
            res = confirm_and_send_queue_item(queue_id=int(it["id"]))
            results.append(res)
        except Exception as e:
            results.append({"ok": False, "queue_id": it["id"], "error": str(e)})
    return {"processed_count": len(results), "results": results}



@router.get("/export")
def api_export_outreach_ready(
    format: str = Query("json", description="'json' ou 'csv'"),
    min_score: int = Query(0, ge=0, le=100),
    assigned_to: Optional[str] = Query(None),
):
    leads = list_leads(min_score=min_score, assigned_to=assigned_to, limit=500)
    if format.lower() == "csv":
        buf = io.StringIO()
        fieldnames = [
            "id",
            "title",
            "city",
            "niche_slug",
            "phone",
            "whatsapp_clean",
            "emails",
            "instagram",
            "website",
            "suggested_domain",
            "domain_available_br",
            "opportunity_score",
            "primary_pain",
            "recommended_service",
            "assigned_to",
            "lead_status",
            "whatsapp_script",
            "whatsapp_url",
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for l in leads:
            sc = l.get("outreach_scripts") or {}
            writer.writerow(
                {
                    "id": l.get("id"),
                    "title": l.get("title"),
                    "city": l.get("city"),
                    "niche_slug": l.get("niche_slug"),
                    "phone": l.get("phone"),
                    "whatsapp_clean": l.get("whatsapp_clean"),
                    "emails": l.get("emails"),
                    "instagram": l.get("instagram"),
                    "website": l.get("website"),
                    "suggested_domain": l.get("suggested_domain"),
                    "domain_available_br": l.get("domain_available_br"),
                    "opportunity_score": l.get("opportunity_score"),
                    "primary_pain": l.get("primary_pain"),
                    "recommended_service": l.get("recommended_service"),
                    "assigned_to": l.get("assigned_to"),
                    "lead_status": l.get("lead_status"),
                    "whatsapp_script": sc.get("whatsapp", ""),
                    "whatsapp_url": sc.get("whatsapp_url", ""),
                }
            )
        return PlainTextResponse(
            content=buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=leads_outreach.csv"},
        )
    return {"count": len(leads), "leads": leads}
