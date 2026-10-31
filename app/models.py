from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchJobRequest(BaseModel):
    city: str = Field(..., description="Cidade alvo (ex: Campinas)")
    state: str = Field("SP", description="UF (ex: SP)")
    niche_slugs: List[str] = Field(default_factory=list, description="Slugs dos nichos selecionados")
    custom_keywords: List[str] = Field(default_factory=list, description="Palavras-chave extras opcionais")
    depth: int = Field(5, ge=1, le=30, description="Profundidade de scroll no Google Maps")
    grid_size: int = Field(1, ge=1, le=5, description="Grade N x N para passar do limite de 120 resultados")
    include_socials: bool = Field(True, description="Extrair Instagram, Facebook e LinkedIn do site")
    run_xray: bool = Field(True, description="Executar motor completo de Raio-X (Registro.br, Health, CMS, Wayback)")
    source_mode: str = Field("auto", description="'google_maps', 'casadosdados', 'demo' ou 'auto'")
    skip_live_network: bool = Field(False, description="Modo rápido sem bloqueio de rede externa por lead")


class LeadManagementUpdate(BaseModel):
    assigned_to: Optional[str] = Field(None, description="'nao_atribuido', 'eu' ou 'amigo'")
    lead_status: Optional[str] = Field(
        None,
        description="'novo', 'analisado', 'contatado', 'respondeu', 'reuniao', 'fechado', 'descartado'",
    )
    notes: Optional[str] = None


class ManualLeadCreate(BaseModel):
    title: str
    category: str = "Empresa Local"
    phone: str = ""
    emails: str = ""
    website: str = ""
    address: str = ""
    city: str = ""
    state: str = "SP"
    niche_slug: str = "geral"
    review_rating: float = 0.0
    review_count: int = 0
    cnpj: str = ""
    opened_date: str = ""
    source: str = "manual"
    run_xray: bool = True


class OutreachEnqueueRequest(BaseModel):
    lead_ids: List[int]
    channels: List[str] = Field(default_factory=lambda: ["whatsapp"])
    scheduled_for: Optional[str] = None


class OutreachClaimRequest(BaseModel):
    channel: str = "whatsapp"
    worker_id: str = "default-worker"


class OutreachStatusUpdate(BaseModel):
    status: str = Field(..., description="'ready', 'sending', 'sent', 'replied', 'failed'")
    external_message_id: Optional[str] = None
    webhook_response: Optional[Dict[str, Any]] = None
