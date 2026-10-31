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
    check_site_availability_and_ssl,
    discover_companies_by_cnae_and_city,
    lookup_cnpj_embedded,
)
from app.services.maps_scraper import (
    build_keywords_for_job,
    check_scraper_engine_health,
    delete_engine_job,
    generate_sample_leads_for_niches,
    geocode_city_embedded,
    list_engine_jobs,
    parse_csv_content_to_leads,
    run_live_maps_scrape,
    start_scraper_engine_docker,
)
from app.services.outreach_generator import (
    build_executive_summary_report,
    build_ready_report_for_lead,
    process_and_save_lead,
    process_leads_batch,
)
from app.services.site_xray import (
    check_wayback_machine,
    run_embedded_site_xray_by_url,
)

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


class CnpjDiscoverRequest(BaseModel):
    city: str = "Campinas"
    state: str = "SP"
    niche_slugs: List[str] = ["clinicas-odontologicas", "escritorios-advocacia"]
    days_opened: int = 90
    import_as_leads: bool = False


@router.get("/discovery/casadosdados")
def api_casadosdados_links(
    city: str = Query("Campinas"),
    state: str = Query("SP"),
    niche_slugs: Optional[str] = Query(None, description="Slugs separados por vírgula"),
) -> List[Dict[str, Any]]:
    slugs = [s.strip() for s in (niche_slugs or "").split(",") if s.strip()]
    return build_casadosdados_links(city=city, state=state, niche_slugs=slugs)


@router.get("/discovery/registro-br")
def api_check_registro_br(
    domain: str = Query(..., description="Domínio .com.br ou nome da empresa"),
    city: str = Query("", description="Cidade opcional para gerar variações .com.br"),
) -> Dict[str, Any]:
    return check_registro_br_availability(domain, city=city)


# ==============================================================================
# ENDPOINTS EMBUTIDOS DAS 8 FERRAMENTAS NATIVAS DO PAINEL (ZERO LINKS EXTERNOS)
# ==============================================================================

@router.get("/tools/maps-engine")
def api_tool_maps_engine(
    city: str = Query("Campinas"),
    state: str = Query("SP"),
    grid_size: int = Query(1, ge=1, le=5),
) -> Dict[str, Any]:
    """Módulo 1 Embutido: Status do motor Docker Google Maps Scraper, lista de jobs e Geocoding Nominatim + Malha."""
    engine = list_engine_jobs()
    geo = geocode_city_embedded(city=city, state=state, grid_size=grid_size)
    return {
        "engine": engine,
        "geocoding": geo,
    }


@router.delete("/tools/maps-engine/jobs/{engine_job_id}")
def api_tool_delete_maps_job(engine_job_id: str) -> Dict[str, Any]:
    """Remove um job diretamente do container Docker gmaps-scraper."""
    return delete_engine_job(engine_job_id)


@router.get("/tools/cnpj")
def api_tool_lookup_cnpj(
    cnpj: str = Query(..., description="CNPJ com 14 dígitos (formatado ou apenas números)"),
    import_as_lead: bool = Query(False, description="Se True, salva a empresa consultada diretamente como Lead"),
    niche_slug: str = Query("geral"),
) -> Dict[str, Any]:
    """Módulo 2 Embutido: Consulta CNPJ na Receita Federal / BrasilAPI com QSA, CNAE, Capital Social e Contato."""
    info = lookup_cnpj_embedded(cnpj)
    if not info.get("valid"):
        raise HTTPException(status_code=400, detail=info.get("error", "CNPJ inválido"))

    saved_lead = None
    if import_as_lead:
        raw_lead = {
            "niche_slug": niche_slug,
            "title": info.get("nome_fantasia") or info.get("razao_social") or "Empresa CNPJ",
            "category": info.get("cnae_fiscal_descricao") or "Empresa CNPJ",
            "phone": info.get("telefone") or "",
            "emails": info.get("email") or "",
            "website": "",
            "address": f"{info.get('logradouro', '')} - {info.get('bairro', '')}".strip(" -"),
            "city": info.get("municipio") or "Campinas",
            "state": info.get("uf") or "SP",
            "cnpj": info.get("cnpj_formatted") or cnpj,
            "opened_date": info.get("data_inicio_atividade") or "",
            "source": "receita_cnpj_embutido",
        }
        saved_lead = process_and_save_lead(raw_lead, run_xray=True, skip_live_network=True)

    return {
        "cnpj_data": info,
        "imported_lead": saved_lead,
    }


@router.post("/tools/cnpj-discover")
def api_tool_discover_companies_by_cnae(payload: CnpjDiscoverRequest) -> Dict[str, Any]:
    """Módulo 2 Embutido: Descobre empresas recém-abertas por Cidade + UF + CNAE e opcionalmente importa como Leads."""
    discovery = discover_companies_by_cnae_and_city(
        city=payload.city,
        state=payload.state,
        niche_slugs=payload.niche_slugs,
        days_opened=payload.days_opened,
    )
    imported_leads = []
    if payload.import_as_leads:
        for comp in discovery.get("companies", []):
            raw_lead = {
                "niche_slug": comp["niche_slug"],
                "title": comp["nome_fantasia"],
                "category": comp["niche_name"],
                "phone": comp["phone"],
                "emails": comp["email"],
                "website": "",
                "address": comp["address"],
                "city": comp["city"],
                "state": comp["state"],
                "cnpj": comp["cnpj"],
                "opened_date": comp["opened_date"],
                "source": "cnae_recem_abertas",
            }
            saved = process_and_save_lead(raw_lead, run_xray=True, skip_live_network=True)
            imported_leads.append(saved)

    return {
        "discovery": discovery,
        "imported_count": len(imported_leads),
        "imported_leads": imported_leads,
    }


@router.get("/tools/registro-br")
def api_tool_registro_br(
    query: str = Query(..., description="Domínio .com.br ou Nome da Empresa"),
    city: str = Query("Campinas"),
) -> Dict[str, Any]:
    """Módulo 3 Embutido: Scanner Oficial RDAP Registro.br com Titular, CNPJ, Expiração, DNS e 3 Variações."""
    return check_registro_br_availability(query, city=city)


@router.get("/tools/site-health")
def api_tool_site_health(url: str = Query(..., description="URL ou domínio do site a verificar")) -> Dict[str, Any]:
    """Módulo 4 Embutido: Monitor HTTP / DNS / SSL (IP resolvido, Certificado TLS, Status HTTP e Latência ms)."""
    res = check_site_availability_and_ssl(url)
    res.pop("html_sample", None)
    return res


@router.get("/tools/site-xray")
def api_tool_site_xray(
    url: str = Query(..., description="URL ou domínio para Raio-X Completo"),
    company_name: str = Query(""),
    city: str = Query("Campinas"),
) -> Dict[str, Any]:
    """Módulos 3 a 8 Embutidos: Executa BuiltWith + Wappalyzer + WhatCMS + Web Archive CDX + DNS/SSL + RDAP."""
    return run_embedded_site_xray_by_url(url_or_domain=url, company_name=company_name, city=city)


@router.get("/tools/wayback")
def api_tool_wayback(url: str = Query(..., description="URL ou domínio para histórico Web Archive CDX")) -> Dict[str, Any]:
    """Módulo 8 Embutido: Scanner Histórico Web Archive CDX + Timeline de Capturas e Dias sem Atualização."""
    return check_wayback_machine(url)


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
    engine_online = engine_health.get("online", False)
    use_live_engine = (not payload.skip_live_network) and (
        payload.source_mode == "google_maps"
        or (payload.source_mode == "auto" and engine_online)
    )

    if payload.source_mode in ("auto", "google_maps") and not payload.skip_live_network and not engine_online:
        update_search_job(job_id, status="failed", error_message="Motor Google Maps (Docker) offline")
        raise HTTPException(
            status_code=503,
            detail="O motor do Google Maps (Docker, porta 8080) está desligado. Suba o container 'gmaps-scraper' para buscar empresas reais.",
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
            force_skip = False
        else:
            raw_leads = generate_sample_leads_for_niches(
                city=payload.city,
                state=payload.state,
                niche_slugs=payload.niche_slugs,
                job_id=job_id,
            )
            force_skip = True

        processed_leads = process_leads_batch(
            raw_leads,
            run_xray=payload.run_xray,
            force_skip_network=force_skip,
        )

        update_search_job(job_id, status="completed", total_found=len(processed_leads))
        return {
            "job": get_search_job(job_id),
            "used_live_docker_engine": use_live_engine,
            "total_leads_processed": len(processed_leads),
            "executive_summary": build_executive_summary_report(processed_leads, city=payload.city),
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


def _ensure_ready_report(lead: Dict[str, Any]) -> Dict[str, Any]:
    sc = lead.get("outreach_scripts")
    if not isinstance(sc, dict):
        sc = {}
    if "ready_report" not in sc:
        sc["ready_report"] = build_ready_report_for_lead(lead, lead, lead)
        lead["outreach_scripts"] = sc
    return lead


@router.get("/reports/summary")
def api_get_executive_summary(city: Optional[str] = Query(None)) -> Dict[str, Any]:
    leads = list_leads(city=city, limit=500)
    return build_executive_summary_report(leads, city=city or "")


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
    rows = list_leads(
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
    return [_ensure_ready_report(r) for r in rows]


@router.get("/leads/{lead_id}")
def api_get_lead(lead_id: int) -> Dict[str, Any]:
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return _ensure_ready_report(lead)


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
