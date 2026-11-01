from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.database import get_landing_page_by_lead, get_landing_page_by_slug
from app.services.landing_generator import generate_landing_for_lead

router = APIRouter(tags=["Landing Pages de Demonstração"])


def _public(page: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "lead_id": page["lead_id"],
        "slug": page["slug"],
        "template": page["template"],
        "content_source": page["content_source"],
        "version": page["version"],
        "url": f"/demo/{page['slug']}",
    }


@router.post("/api/leads/{lead_id}/landing")
def api_generate_landing(lead_id: int, use_llm: bool = Query(True)) -> Dict[str, Any]:
    page = generate_landing_for_lead(lead_id, use_llm=use_llm)
    if not page:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return _public(page)


@router.get("/api/leads/{lead_id}/landing")
def api_get_landing(lead_id: int) -> Dict[str, Any]:
    page = get_landing_page_by_lead(lead_id)
    if not page:
        raise HTTPException(status_code=404, detail="Landing ainda não gerada")
    return _public(page)


@router.get("/demo/{slug}", response_class=HTMLResponse, include_in_schema=False)
def serve_demo(slug: str) -> HTMLResponse:
    page = get_landing_page_by_slug(slug)
    if not page:
        raise HTTPException(status_code=404, detail="Demo não encontrada")
    return HTMLResponse(page["html"], headers={"X-Robots-Tag": "noindex, nofollow"})
