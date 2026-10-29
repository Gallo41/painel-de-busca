from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import (
    create_search_job,
    get_dashboard_stats,
    get_lead,
    get_search_job,
    list_leads,
    list_niches,
    list_search_jobs,
    update_lead_management,
    update_search_job,
)
from app.models import LeadManagementUpdate, ManualLeadCreate, SearchJobRequest
from app.services.business_discovery import (
    build_casadosdados_links,
    check_registro_br_availability,
)
from app.services.maps_scraper import (
    build_keywords_for_job,
    check_scraper_engine_health,
    generate_sample_leads_for_niches,
    parse_csv_content_to_leads,
    run_live_maps_scrape,
    start_scraper_engine_docker,
)
from app.services.outreach_generator import process_and_save_lead

router = APIRouter(prefix="/api", tags=["Leads, Buscas & Raio-X"])


class CsvImportRequest(BaseModel):
    csv_text: str
    city: str = "Campinas"
    state: str = "SP"
    niche_slug: str = "geral"
    run_xray: bool = True


@router.get("/health")
def api_health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "scraper_engine": check_scraper_engine_health(),
        "stats": get_dashboard_stats(),
    }


@router.post("/engine/start")
def api_start_engine() -> Dict[str, Any]:
    return start_scraper_engine_docker()


@router.get("/niches")
def api_list_niches() -> List[Dict[str, Any]]:
    return list_niches(active_only=True)


@router.get("/discovery/casadosdados")
def api_casadosdados_links(
    city: str = Query("Campinas"),
    state: str = Query("SP"),
    niche_slugs: Optional[str] = Query(None, description="Slugs separados por vírgula"),
) -> List[Dict[str, Any]]:
    slugs = [s.strip() for s in (niche_slugs or "").split(",") if s.strip()]
    return build_casadosdados_links(city=city, state=state, niche_slugs=slugs)


@router.get("/discovery/registro-br")
def api_check_registro_br(domain: str = Query(..., description="Domínio .com.br ou nome da empresa")) -> Dict[str, Any]:
    return check_registro_br_availability(domain)


@router.get("/jobs")
def api_list_jobs(limit: int = Query(30, ge=1, le=100)) -> List[Dict[str, Any]]:
    return list_search_jobs(limit=limit)


@router.post("/jobs")
def api_create_and_run_job(payload: SearchJobRequest) -> Dict[str, Any]:
    keywords = build_keywords_for_job(
        city=payload.city,
        state=payload.state,
        niche_slugs=payload.niche_slugs,
        custom_keywords=payload.custom_keywords,
    )
    job_id = create_search_job(
        city=payload.city,
        state=payload.state,
        niche_slugs=payload.niche_slugs,
        keywords=keywords,
        depth=payload.depth,
        grid_size=payload.grid_size,
        include_socials=payload.include_socials,
        source_mode=payload.source_mode,
    )
    update_search_job(job_id, status="running")

    engine_health = check_scraper_engine_health()
    use_live_engine = payload.source_mode == "google_maps" or (
        payload.source_mode == "auto" and engine_health.get("online", False)
    )

    try:
        if use_live_engine:
            raw_leads = run_live_maps_scrape(
                city=payload.city,
                state=payload.state,
                niche_slugs=payload.niche_slugs,
                custom_keywords=payload.custom_keywords,
                depth=payload.depth,
                grid_size=payload.grid_size,
                include_socials=payload.include_socials,
                job_id=job_id,
            )
            skip_net = False
        else:
            raw_leads = generate_sample_leads_for_niches(
                city=payload.city,
                state=payload.state,
                niche_slugs=payload.niche_slugs,
                job_id=job_id,
            )
            skip_net = payload.source_mode == "demo"

        processed_leads = []
        for raw in raw_leads:
            saved = process_and_save_lead(
                raw,
                run_xray=payload.run_xray,
                skip_live_network=skip_net,
            )
            processed_leads.append(saved)

        update_search_job(job_id, status="completed", total_found=len(processed_leads))
        return {
            "job": get_search_job(job_id),
            "used_live_docker_engine": use_live_engine,
            "total_leads_processed": len(processed_leads),
            "leads": processed_leads,
            "casadosdados_filters": build_casadosdados_links(
                city=payload.city,
                state=payload.state,
                niche_slugs=payload.niche_slugs,
            ),
        }
    except Exception as exc:
        update_search_job(job_id, status="failed", error_message=str(exc))
        raise HTTPException(status_code=500, detail=f"Falha ao executar busca: {exc}")


@router.post("/leads/import-csv")
def api_import_csv(payload: CsvImportRequest) -> Dict[str, Any]:
    raw_leads = parse_csv_content_to_leads(
        payload.csv_text,
        city=payload.city,
        state=payload.state,
        niche_slug=payload.niche_slug,
    )
    saved_list = [
        process_and_save_lead(item, run_xray=payload.run_xray)
        for item in raw_leads
    ]
    return {"imported_count": len(saved_list), "leads": saved_list}


@router.post("/leads")
def api_create_manual_lead(payload: ManualLeadCreate) -> Dict[str, Any]:
    lead_dict = payload.model_dump()
    run_xray = lead_dict.pop("run_xray", True)
    return process_and_save_lead(lead_dict, run_xray=run_xray, skip_live_network=True)


@router.get("/leads")
def api_list_leads(
    niche_slug: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    primary_pain: Optional[str] = Query(None),
    recommended_service: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    lead_status: Optional[str] = Query(None),
    min_score: int = Query(0, ge=0, le=100),
    only_domain_available: bool = Query(False),
    search_query: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=500),
) -> List[Dict[str, Any]]:
    return list_leads(
        niche_slug=niche_slug,
        city=city,
        primary_pain=primary_pain,
        recommended_service=recommended_service,
        assigned_to=assigned_to,
        lead_status=lead_status,
        min_score=min_score,
        only_domain_available=only_domain_available,
        search_query=search_query,
        limit=limit,
    )


@router.get("/leads/{lead_id}")
def api_get_lead(lead_id: int) -> Dict[str, Any]:
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead


@router.patch("/leads/{lead_id}")
def api_update_lead(lead_id: int, payload: LeadManagementUpdate) -> Dict[str, Any]:
    updated = update_lead_management(
        lead_id=lead_id,
        assigned_to=payload.assigned_to,
        lead_status=payload.lead_status,
        notes=payload.notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return updated


@router.post("/leads/{lead_id}/reanalyze")
def api_reanalyze_lead(lead_id: int) -> Dict[str, Any]:
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return process_and_save_lead(lead, run_xray=True, skip_live_network=False)
