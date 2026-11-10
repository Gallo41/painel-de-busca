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
        description="'novo', 'vou_fazer', 'fazendo', 'nao_fazer', 'fechado', 'analisado', 'contatado', 'respondeu', 'reuniao', 'descartado'",
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


class QueuePrepareBatchRequest(BaseModel):
    day: int = Field(1, ge=1, le=60, description="Dia do plano de disparo (1 = próximos melhores)")
    per_day: int = Field(20, ge=1, le=100, description="Tamanho do lote")
    segment: Optional[str] = Field(None, description="Slug do nicho real (ex: odontologia)")
    tiers: List[str] = Field(default_factory=lambda: ["A", "B", "C"])
    only_missing_to_target: bool = Field(
        False,
        description="Se True, apenas completa a fila até atingir `per_day` itens ready",
    )


class OutreachClaimRequest(BaseModel):
    channel: str = "whatsapp"
    worker_id: str = "default-worker"


class OutreachStatusUpdate(BaseModel):
    status: str = Field(..., description="'ready', 'sending', 'sent', 'replied', 'failed'")
    external_message_id: Optional[str] = None
    webhook_response: Optional[Dict[str, Any]] = None


class AgentSettingsUpdate(BaseModel):
    test_mode: Optional[bool] = None
    auto_send_enabled: Optional[bool] = None
    auto_prepare_queue: Optional[bool] = None
    auto_prepare_batch_size: Optional[int] = Field(None, ge=1, le=100)
    boss_phone: Optional[str] = None
    test_client_phone: Optional[str] = None
    attendant_name: Optional[str] = None
    company_name: Optional[str] = None
    bridge_url: Optional[str] = None
    uazapi_url: Optional[str] = None
    uazapi_token: Optional[str] = None
    debounce_seconds: Optional[float] = Field(None, ge=0.0, le=30.0)
    pause_minutes_on_human: Optional[int] = Field(None, ge=1, le=10080)


class QueueConfirmSendRequest(BaseModel):
    custom_message: Optional[str] = None


class AgentWebhookPayload(BaseModel):
    EventType: Optional[str] = "messages"
    instanceName: Optional[str] = None
    message: Optional[Dict[str, Any]] = None


class ConversationControlRequest(BaseModel):
    reason: Optional[str] = "intervencao_manual_painel"
    pause_minutes: Optional[int] = None


class BossManualReplyRequest(BaseModel):
    reply_text: str


class PrototypeGenerateRequest(BaseModel):
    custom_instructions: Optional[str] = None
    scope_override: Optional[str] = None

