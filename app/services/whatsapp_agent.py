import json
import re
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from app.database import (
    append_agent_message,
    br_phone_variants,
    create_or_activate_agent_conversation,
    create_price_consultation,
    delete_agent_messages_after,
    get_active_conversation_by_chatid,
    get_agent_conversation,
    get_agent_settings,
    get_lead,
    get_pending_price_consultation,
    list_agent_messages,
     list_outreach_queue,
    normalize_phone_digits,
    phones_match_br,
    resolve_price_consultation,
    update_agent_conversation,
    update_lead_management,
    update_outreach_status,
)
from app.services.ai_provider import call_llm_chat

# Log em memória dos envios realizados na sessão (útil para auditoria no Painel e testes)
OUTBOX_LOG: List[Dict[str, Any]] = []

# Buffers de agrupamento (Cicatriz #2: cliente escreve picado no WhatsApp)
_BUFFERS: Dict[str, Dict[str, Any]] = {}
_BUFFER_LOCK = threading.Lock()

DIAS_SEMANA = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]

CATALOGO_SOLUCOES: Dict[str, Dict[str, Any]] = {
    "LANDING_PAGE": {
        "codigo": "LANDING_PAGE",
        "nome": "Landing Page de Alta Conversão",
        "faixa_preco": "R$ 900 a R$ 1.800",
        "preco_sugerido_cents": 139000,
        "prazo_medio": "3 a 5 dias úteis",
        "resultado": (
            "transformar quem pesquisa no Google ou visita o Instagram em cliente chamando direto no WhatsApp, "
            "com apresentação profissional, prova social, catálogo enxuto e botão de ação rápida"
        ),
    },
    "SITE_INSTITUCIONAL": {
        "codigo": "SITE_INSTITUCIONAL",
        "nome": "Site Profissional Completo + Posicionamento Google",
        "faixa_preco": "R$ 1.600 a R$ 2.900",
        "preco_sugerido_cents": 219000,
        "prazo_medio": "5 a 8 dias úteis",
        "resultado": (
            "posicionar a empresa no Google na cidade para múltiplos serviços, gerando autoridade e captação "
            "constante de orçamentos no WhatsApp"
        ),
    },
    "SISTEMA_SOB_MEDIDA": {
        "codigo": "SISTEMA_SOB_MEDIDA",
        "nome": "Sistema Web / Painel Operacional e Agendamento (Sem Módulo Fiscal)",
        "faixa_preco": "R$ 2.500 a R$ 5.500",
        "preco_sugerido_cents": 349000,
        "prazo_medio": "7 a 15 dias úteis",
        "resultado": (
            "automatizar agendamentos, organizar pedidos/clientes e ter um painel comercial sob medida na web, "
            "100% focado em vendas e operação (sem parte fiscal/tributária)"
        ),
    },
}

FISCAL_KEYWORDS_REGEX = re.compile(
    r"\b(nota\s+fiscal|notas\s+fiscais|nf-?e|nfc-?e|nfs-?e|cupom\s+fiscal|sat\s+fiscal|sefaz|"
    r"sped|imposto|impostos|tribut[aá]ri[oa]|emissor\s+fiscal|contabilidade\s+fiscal|danfe)\b",
    re.IGNORECASE,
)

PRICE_INQUIRY_REGEX = re.compile(
    r"\b(quanto\s+custa|qual\s+o\s+valor|qual\s+o\s+pre[cç]o|pre[cç]o|valor|valores|or[cç]amento|"
    r"investimento|fica\s+quanto|sai\s+quanto|cobram\s+quanto|parcela|condi[cç][aã]o)\b",
    re.IGNORECASE,
)

BEYOND_LP_REGEX = re.compile(
    r"\b(sistema|painel|agendamento|agenda\s+online|cadastro\s+de\s+clientes|controle\s+de\s+pedidos|"
    r"area\s+do\s+cliente|[aá]rea\s+restrita|login|cat[aá]logo\s+completo|portal|plataforma|dashboard)\b",
    re.IGNORECASE,
)

CLOSE_DEAL_REGEX = re.compile(
    r"\b(fechado|pode\s+fazer|vamos\s+fechar|bora\s+fechar|quero\s+fechar|aprovo|aprovado|"
    r"manda\s+o\s+prot[oó]tipo|faz\s+o\s+prot[oó]tipo|pode\s+montar|vamos\s+fazer|topo\s+fazer|"
    r"fechou)\b",
    re.IGNORECASE,
)


def moeda_br(valor_centavos: int) -> str:
    """
    Cicatriz #5: Formata dinheiro SEMPRE no código, nunca no modelo.
    Ex: 139000 (centavos) -> 'R$ 1.390'
    """
    reais = int(round(valor_centavos / 100.0))
    formatado = f"{reais:,}".replace(",", ".")
    return f"R$ {formatado}"


def bloco_de_datas(tz_name: str = "America/Sao_Paulo") -> str:
    """
    Cicatriz #7: Container em UTC erra o dia da semana.
    Calcula hoje e os próximos 7 dias no timezone correto a cada turno.
    """
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone(timedelta(hours=-3))
    agora = datetime.now(tz)
    linhas = []
    for i in range(7):
        d = agora + timedelta(days=i)
        dia_sem = DIAS_SEMANA[d.weekday()]
        data_str = d.strftime("%d/%m")
        prefixo = "hoje" if i == 0 else ("amanhã" if i == 1 else dia_sem)
        linhas.append(f"- {prefixo} ({dia_sem}, {data_str})")
    hora_str = agora.strftime("%H:%M")
    return f"Agora são {hora_str}. Próximos dias:\n" + "\n".join(linhas)


def limpar_texto_whatsapp(texto: str) -> str:
    """
    Cicatriz #4/Saída: Remove formatação de documento/e-mail que denuncia robô no WhatsApp.
    """
    if not texto:
        return ""
    limpo = texto.replace("\r\n", "\n")
    limpo = re.sub(r"\*\*([^*]+)\*\*", r"\1", limpo)
    limpo = re.sub(r"^\s*[-*•]\s+", "", limpo, flags=re.MULTILINE)
    limpo = re.sub(r"\n{2,}", " ", limpo)
    limpo = re.sub(r"[ \t]{2,}", " ", limpo).strip()
    # Remove clichês robóticos corporativos caso algum modelo tente usá-los
    for cliche in (
        "Prezado cliente,",
        "Prezado(a),",
        "Como posso ajudá-lo hoje?",
        "Fico feliz em informar que",
        "Agradecemos o seu contato.",
        "Estou à disposição para",
    ):
        limpo = re.sub(re.escape(cliche), "", limpo, flags=re.IGNORECASE).strip()
    return limpo


def detect_fiscal_request(texto: str) -> bool:
    return bool(FISCAL_KEYWORDS_REGEX.search(texto or ""))


def detect_scope_from_text(texto: str, current_scope: str = "LANDING_PAGE") -> str:
    if BEYOND_LP_REGEX.search(texto or ""):
        return "SISTEMA_SOB_MEDIDA"
    if re.search(r"\b(site\s+completo|v[aá]rias\s+p[aá]ginas|institucional)\b", texto or "", re.IGNORECASE):
        return "SITE_INSTITUCIONAL"
    return current_scope or "LANDING_PAGE"


# ---------------------------------------------------------------------------
# Cliente HTTP para o Micro-Bridge QR Code (Baileys) ou UAZAPI
# ---------------------------------------------------------------------------


def _resolve_transport_endpoint(settings: Dict[str, Any]) -> Tuple[str, Dict[str, str], str]:
    uazapi_url = (settings.get("uazapi_url") or "").strip().rstrip("/")
    uazapi_token = (settings.get("uazapi_token") or "").strip()
    if uazapi_url and uazapi_token:
        return uazapi_url, {"Content-Type": "application/json", "token": uazapi_token}, "uazapi"

    bridge_url = (settings.get("bridge_url") or "http://127.0.0.1:3100").strip().rstrip("/")
    return bridge_url, {"Content-Type": "application/json"}, "qr_bridge"


def get_bridge_status(db_path: Optional[str] = None) -> Dict[str, Any]:
    settings = get_agent_settings(db_path)
    base_url, headers, mode = _resolve_transport_endpoint(settings)
    try:
        req = urllib.request.Request(f"{base_url}/status", headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            data["transport_mode"] = mode
            data["bridge_url"] = base_url
            return data
    except Exception as e:
        return {
            "connected": False,
            "status": "bridge_offline",
            "transport_mode": mode,
            "bridge_url": base_url,
            "qr_data_url": None,
            "detail": f"Micro-bridge QR Code ainda não iniciado em {base_url} ({e}). O Agente opera normalmente em modo simulado/painel até conectar.",
        }


def send_whatsapp_text(
    chatid: str,
    text: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Envia mensagem de texto pelo Bridge QR Code ou UAZAPI (`POST /send/text`).
    Registra sempre no `OUTBOX_LOG` para auditoria no Painel e resiliência em testes.
    """
    numero = normalize_phone_digits(chatid)
    if not numero:
        raise ValueError(f"chatid inválido: {chatid}")

    settings = get_agent_settings(db_path)
    base_url, headers, mode = _resolve_transport_endpoint(settings)
    payload = {"number": numero, "text": text, "linkPreview": False}

    delivered_live = False
    external_id = f"local-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    error_detail = ""

    try:
        req = urllib.request.Request(
            f"{base_url}/send/text",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=6.0) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            body = json.loads(raw) if raw.strip().startswith("{") else {}
            delivered_live = True
            external_id = str(body.get("messageid") or body.get("id") or external_id)
    except Exception as e:
        error_detail = str(e)

    entry = {
        "number": numero,
        "text": text,
        "delivered_live": delivered_live,
        "transport_mode": mode,
        "external_message_id": external_id,
        "error": error_detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    OUTBOX_LOG.append(entry)
    return entry


def mark_whatsapp_read(message_ids: List[str], db_path: Optional[str] = None) -> None:
    """Enfeite de humanização: 2 tiques azuis. Falha em silêncio (Cicatriz whatsapp.ts)."""
    if not message_ids:
        return
    settings = get_agent_settings(db_path)
    base_url, headers, _ = _resolve_transport_endpoint(settings)
    try:
        req = urllib.request.Request(
            f"{base_url}/message/markread",
            data=json.dumps({"id": message_ids}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2.0).read()
    except Exception:
        pass


def send_whatsapp_presence(chatid: str, presence: str = "composing", db_path: Optional[str] = None) -> None:
    """
    Cicatriz #6: O endpoint /message/presence exige o campo `number` (apenas dígitos), não `chatId`.
    Falha em silêncio se o bridge estiver desconectado.
    """
    numero = normalize_phone_digits(chatid)
    if not numero:
        return
    settings = get_agent_settings(db_path)
    base_url, headers, _ = _resolve_transport_endpoint(settings)
    try:
        req = urllib.request.Request(
            f"{base_url}/message/presence",
            data=json.dumps({"number": numero, "presence": presence}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2.0).read()
    except Exception:
        pass


def responder_como_humano(
    chatid: str,
    texto: str,
    ids_recebidos: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    mark_whatsapp_read(ids_recebidos or [], db_path=db_path)
    send_whatsapp_presence(chatid, "composing", db_path=db_path)
    return send_whatsapp_text(chatid, texto, db_path=db_path)


# ---------------------------------------------------------------------------
# Controle de Pausa / Handoff Humano (90% dos casos)
# ---------------------------------------------------------------------------


def pause_conversation(
    conversation_id: int,
    minutes: int = 60,
    reason: str = "humano_assumiu_conversa",
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    ate = (datetime.now(timezone.utc) + timedelta(minutes=max(1, minutes))).isoformat()
    conv = get_agent_conversation(conversation_id, db_path)
    if conv and conv.get("paused_until") and conv["paused_until"] > ate:
        ate = conv["paused_until"]
    return update_agent_conversation(
        conversation_id=conversation_id,
        status="paused_by_human",
        paused_until=ate,
        pause_reason=reason,
        increment_turn=True,
        db_path=db_path,
    )


def resume_conversation(conversation_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return update_agent_conversation(
        conversation_id=conversation_id,
        status="active",
        paused_until=None,
        pause_reason="",
        increment_turn=True,
        db_path=db_path,
    )


def is_conversation_paused(conv: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    if not conv:
        return False
    paused_until = conv.get("paused_until")
    if conv.get("status") == "paused_by_human" and paused_until:
        now_iso = datetime.now(timezone.utc).isoformat()
        if now_iso < paused_until:
            return True
        # Expirou a pausa: reativa conversa
        update_agent_conversation(
            conv["id"],
            status="active",
            paused_until=None,
            pause_reason="",
            db_path=db_path,
        )
        return False
    return conv.get("status") == "paused_by_human"


# ---------------------------------------------------------------------------
# Confirmação na Fila -> Disparo da 1ª Mensagem e Autorização de Negociação
# ---------------------------------------------------------------------------


def confirm_and_send_queue_item(
    queue_id: int,
    custom_message: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Acionado quando o usuário confirma o lead na fila do Painel.
    - Se `test_mode=True` nas configurações, redireciona o envio para `test_client_phone` (+55 19 99610-9028),
      mantendo todos os dados e diagnóstico do lead real para simulação fiel.
    - Se `test_mode=False`, envia para o número real do lead.
    - Cria/ativa a conversa em `agent_conversations`, envia a 1ª mensagem e autoriza o agente a negociar.
    """
    items = list_outreach_queue(limit=500, db_path=db_path)
    item = next((x for x in items if int(x["id"]) == int(queue_id)), None)
    if not item:
        raise ValueError(f"Item #{queue_id} não encontrado na fila de outreach")

    lead_id = int(item["lead_id"])
    lead = get_lead(lead_id, db_path=db_path)
    if not lead:
        raise ValueError(f"Lead #{lead_id} não encontrado")

    settings = get_agent_settings(db_path)
    is_test = bool(settings.get("test_mode", True))
    real_phone = normalize_phone_digits(item.get("recipient") or lead.get("whatsapp_clean") or lead.get("phone") or "")
    target_chatid = (
        normalize_phone_digits(settings.get("test_client_phone") or "5519996109028")
        if is_test
        else real_phone
    )
    if not target_chatid:
        raise ValueError("Nenhum número de WhatsApp válido encontrado para disparo.")

    body = (custom_message or item.get("message_body") or "").strip()
    if not body:
        scripts = lead.get("outreach_scripts") or {}
        body = (scripts.get("whatsapp") or "").strip()
    if not body:
        body = (
            f"Oi, tudo bem? Vi a {lead.get('title')} aqui em {lead.get('city') or 'sua região'} e notei uma "
            f"oportunidade prática para vocês captarem mais clientes pelo Google com uma página rápida no WhatsApp. "
            f"Com quem eu falo sobre essa parte comercial?"
        )

    conv = create_or_activate_agent_conversation(
        lead_id=lead_id,
        chatid=target_chatid,
        real_lead_phone=real_phone,
        queue_id=queue_id,
        is_test_session=is_test,
        db_path=db_path,
    )

    send_res = responder_como_humano(target_chatid, body, db_path=db_path)
    append_agent_message(
        conversation_id=conv["id"],
        role="model",
        direction="outbound",
        content=body,
        external_message_id=send_res.get("external_message_id", ""),
        db_path=db_path,
    )

    updated_queue = update_outreach_status(
        queue_id=queue_id,
        status="sent",
        external_message_id=send_res.get("external_message_id", ""),
        webhook_response={
            "target_chatid": target_chatid,
            "is_test_mode": is_test,
            "delivered_live": send_res.get("delivered_live", False),
        },
        db_path=db_path,
    )

    return {
        "ok": True,
        "queue_item": updated_queue,
        "conversation": get_agent_conversation(conv["id"], db_path=db_path),
        "target_chatid": target_chatid,
        "is_test_mode": is_test,
        "sent_message": body,
        "delivery": send_res,
    }


# ---------------------------------------------------------------------------
# System Prompt Estruturado (11 Seções da Skill agente-whatsapp)
# ---------------------------------------------------------------------------


def build_agent_system_prompt(
    lead: Dict[str, Any],
    conv: Dict[str, Any],
    settings: Dict[str, Any],
) -> str:
    attendant = settings.get("attendant_name") or "Léo"
    company = settings.get("company_name") or "Estúdio Digital"
    title = lead.get("title") or "sua empresa"
    city = lead.get("city") or "sua região"
    pain_summary = lead.get("pain_summary") or "Ausência de página própria de alta conversão no Google"
    suggested_domain = lead.get("suggested_domain") or ""
    reqs = conv.get("collected_requirements") or {}
    approved_price = conv.get("approved_price_text") or ""

    return f"""1. QUEM VOCÊ É
Você é {attendant}, consultor comercial da {company}, especialista em criar Landing Pages de alta conversão e Sistemas Web sob medida.
Você faz o atendimento consultivo no WhatsApp conversando com a empresa "{title}" ({city}). Seu foco é vender o RESULTADO comercial e preparar o terreno para o fechamento.

2. QUANDO É AGORA
{bloco_de_datas()}

3. CONTEXTO DO CLIENTE (RAIO-X REAL)
- Empresa: {title} ({city})
- Diagnóstico detectado: {pain_summary}
- Sugestão de domínio verificada: {suggested_domain or 'consultar conforme preferência'}
- Requisitos já levantados na conversa: {json.dumps(reqs, ensure_ascii=False)}
- Proposta/Preço aprovado pelo Chefe até agora: {approved_price or 'Ainda em avaliação'}

4. COMO VOCÊ ESCREVE (TOM DESCONTRAÍDO DE WHATSAPP)
- No máximo 2 frases curtas por mensagem.
- Português brasileiro natural, direto, como alguém real digitando do celular.
- Nunca use marcadores, listas com traços, títulos ou negrito excessivo — é WhatsApp, não e-mail.
- Proibido usar frases de robô corporativo ("Como posso ajudá-lo?", "Prezado cliente", "Fico feliz em informar", "Estou à disposição").
- Emoji ocasional, no máximo 1 por mensagem, sem forçar.

5. EXEMPLOS DE CONVERSA
Cliente: Do que se trata?
Você: Analisei a {title} aqui no Google e vi que vocês podem captar muito mais clientes tendo uma página rápida focada em trazer orçamentos direto pro WhatsApp. Hoje os clientes chegam mais por indicação ou pelo Instagram?

Cliente: Já tenho Instagram, pra que preciso de uma página?
Você: O Instagram é ótimo pra quem já te conhece, mas quem pesquisa pelo seu serviço no Google na hora da urgência acaba clicando no concorrente que tem uma Landing Page pronta. Uma página enxuta com botão direto pro seu WhatsApp faz esse cliente cair direto no seu atendimento, faz sentido pra rotina de vocês?

Cliente: E se eu precisar de um sistema com agendamento e emissão de nota fiscal?
Você: A parte de agendamento online e painel comercial de clientes a gente monta sob medida tranquilo. Só a parte fiscal e emissão de nota que nós não fazemos pra não assumir responsabilidade tributária, mas todo o controle comercial e captação fica pronto — vocês preferem algo mais simples ou com painel de horários?

Cliente: Quanto custa pra fazer uma Landing Page?
Você: Uma Landing Page profissional nesse padrão costuma ficar na faixa de R$ 900 a R$ 1.800 dependendo dos recursos. Já mandei o escopo de vocês pro meu sócio fechar uma condição especial pro caso da {title}, quer incluir catálogo ou botão de agendamento nela?

6. SEU OBJETIVO
1. Convencer o cliente do RESULTADO prático (mais clientes do Google chamando no WhatsApp e mais autoridade profissional).
2. Entender se o ideal para ele hoje é uma Landing Page rápida ou algo além de LP (site completo, agendamento, painel de pedidos/clientes).
3. Levantar o que ele gostaria de ter na página/sistema (uma pergunta por vez!).
4. Quando falar de preço ou fechar escopo, informar a faixa base se ele pedir e acionar a consulta com o Chefe ou confirmar o fechamento para geração do protótipo.
Regra de ouro: UMA PERGUNTA POR VEZ. Nunca junte duas perguntas na mesma mensagem.

7. REGRAS DO DOMÍNIO (PROIBIÇÃO FISCAL ABSOLUTA)
- NUNCA aceite, prometa ou inclua emissão de Nota Fiscal (NF-e, NFC-e, NFS-e), cupom fiscal, SAT, impostos ou contabilidade fiscal.
- Se o cliente pedir algo fiscal, explique com naturalidade que vocês atuam 100% na parte comercial, captação de clientes e operação (sem módulo fiscal/tributário) e volte para o benefício comercial.
- Nunca invente preço fora das faixas oficiais ou do valor aprovado pelo Chefe.
"""


# ---------------------------------------------------------------------------
# Ponte de Consulta de Preço em Tempo Real com o Chefe (+551999958516)
# ---------------------------------------------------------------------------


def calculate_suggested_price(scope_type: str, client_text: str) -> Tuple[int, str, Dict[str, Any]]:
    sol = CATALOGO_SOLUCOES.get(scope_type) or CATALOGO_SOLUCOES["LANDING_PAGE"]
    base_cents = int(sol["preco_sugerido_cents"])
    # Pequeno ajuste inteligente conforme complexidade pedida
    if re.search(r"\b(agendamento|cat[aá]logo|painel|login|integra[cç][aã]o)\b", client_text or "", re.IGNORECASE):
        if scope_type == "LANDING_PAGE":
            base_cents = 159000
        elif scope_type == "SISTEMA_SOB_MEDIDA":
            base_cents = 390000
    return base_cents, str(sol["faixa_preco"]), sol


def trigger_boss_price_consultation(
    conv: Dict[str, Any],
    lead: Dict[str, Any],
    client_text: str,
    scope_type: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cria o registro em `price_consultations` e envia WhatsApp imediato para o Chefe (+551999958516)
    com o resumo do lead, faixa informada e sugestão de preço para aprovação rápida.
    """
    settings = get_agent_settings(db_path)
    boss_phone = normalize_phone_digits(settings.get("boss_phone") or "551999958516")
    suggested_cents, faixa_str, sol = calculate_suggested_price(scope_type, client_text)
    sugestao_fmt = moeda_br(suggested_cents)

    consultation = create_price_consultation(
        conversation_id=conv["id"],
        lead_id=lead["id"],
        client_summary=client_text.strip(),
        scope_type=scope_type,
        suggested_price_cents=suggested_cents,
        price_range_text=faixa_str,
        db_path=db_path,
    )

    update_agent_conversation(
        conversation_id=conv["id"],
        status="waiting_boss_price",
        suggested_price_cents=suggested_cents,
        collected_requirements={"escopo_detectado": sol["nome"], "ultimo_pedido_cliente": client_text.strip()},
        db_path=db_path,
    )

    cid = consultation.get("id", 1)
    msg_chefe = (
        f"💰 *[Consulta de Preço #{cid} - {lead.get('title')} ({lead.get('city')})]*\n"
        f"• *Solução*: {sol['nome']}\n"
        f"• *Mensagem do cliente*: \"{client_text.strip()}\"\n"
        f"• *Faixa de referência*: {faixa_str}\n"
        f"💡 *Sugestão do Agente*: {sugestao_fmt} (ou 3x sem juros)\n\n"
        f"Responda aqui com o valor/condição aprovada (ex: `#{cid} pode fazer {sugestao_fmt} à vista ou 3x`) "
        f"para eu enviar agora ao cliente, ou mande `#{cid} assumo` para entrar na conversa."
    )

    delivery = send_whatsapp_text(boss_phone, msg_chefe, db_path=db_path)
    append_agent_message(
        conversation_id=conv["id"],
        role="system",
        direction="outbound",
        content=f"[Consulta #{cid} enviada ao Chefe ({boss_phone}) sugerindo {sugestao_fmt}]",
        external_message_id=delivery.get("external_message_id", ""),
        db_path=db_path,
    )

    return {
        "consultation": consultation,
        "suggested_price_formatted": sugestao_fmt,
        "price_range": faixa_str,
        "solution": sol,
        "boss_delivery": delivery,
    }


def handle_boss_incoming_message(
    boss_chatid: str,
    text: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Processa uma mensagem enviada pelo número do Chefe (+551999958516).
    Permite:
    - Aprovar/definir preço para o cliente (ex: `#1 1350 em 3x` ou apenas `1400 em 3x`)
    - Assumir/pausar a conversa (`#1 assumo` ou `pausar`)
    - Disparar geração de protótipo (`#1 prototipo`)
    """
    clean_text = (text or "").strip()
    m_id = re.search(r"#(\d+)", clean_text)
    explicit_id = int(m_id.group(1)) if m_id else None
    body_without_id = re.sub(r"^#\d+\s*[-:]?\s*", "", clean_text).strip()

    pending = get_pending_price_consultation(consultation_id=explicit_id, db_path=db_path)
    if not pending:
        # Tenta localizar a conversa mais recente se não houver consulta pendente aberta
        from app.database import list_agent_conversations

        convs = list_agent_conversations(limit=1, db_path=db_path)
        if not convs:
            reply = "Nenhuma consulta de preço ou conversa ativa encontrada no momento."
            send_whatsapp_text(boss_chatid, reply, db_path=db_path)
            return {"handled": True, "action": "no_active_consultation", "reply": reply}
        conv = convs[0]
        lead = get_lead(conv["lead_id"], db_path=db_path) or {}
        consultation_id = None
    else:
        consultation_id = int(pending["id"])
        conv = get_agent_conversation(int(pending["conversation_id"]), db_path=db_path) or {}
        lead = get_lead(int(pending["lead_id"]), db_path=db_path) or {}

    if not conv:
        return {"handled": False, "action": "conversation_not_found"}

    # Caso 1: Chefe pediu para assumir/pausar o agente
    if re.search(r"\b(assumo|assumir|pausa|pausar|deixa\s+comigo|eu\s+falo)\b", body_without_id, re.IGNORECASE):
        pause_conversation(conv["id"], minutes=120, reason="chefe_assumiu_via_whatsapp", db_path=db_path)
        ack = f"⏸️ Agente pausado para *{lead.get('title')}*. Pode falar direto com o cliente sem interferência."
        send_whatsapp_text(boss_chatid, ack, db_path=db_path)
        return {"handled": True, "action": "paused_by_boss", "conversation_id": conv["id"]}

    # Caso 2: Chefe pediu para gerar protótipo diretamente
    if re.search(r"\b(gerar\s+prot[oó]tipo|faz\s+o\s+prot[oó]tipo|prot[oó]tipo)\b", body_without_id, re.IGNORECASE):
        from app.services.prototype_generator import generate_prototype_for_lead

        proto = generate_prototype_for_lead(
            lead_id=lead["id"],
            conversation_id=conv["id"],
            custom_instructions=body_without_id,
            notify_boss=True,
            db_path=db_path,
        )
        return {"handled": True, "action": "prototype_generated", "prototype": proto}

    # Caso 3: Chefe enviou o preço/condição aprovada
    # Se digitou apenas um número (ex: "1350"), formata como R$ 1.350
    if re.fullmatch(r"r?\$?\s*\d{3,5}([.,]\d{2})?", body_without_id, flags=re.IGNORECASE):
        digits_only = int(re.sub(r"\D", "", body_without_id.split(",")[0].split(".")[0]))
        formatted_offer = moeda_br(digits_only * 100)
    else:
        formatted_offer = body_without_id

    if consultation_id is not None:
        resolve_price_consultation(consultation_id, formatted_offer, db_path=db_path)

    append_agent_message(
        conversation_id=conv["id"],
        role="boss",
        direction="inbound",
        content=f"[Chefe aprovou condição]: {formatted_offer}",
        db_path=db_path,
    )

    update_agent_conversation(
        conversation_id=conv["id"],
        status="active",
        approved_price_text=formatted_offer,
        db_path=db_path,
    )

    scope_code = (pending or {}).get("scope_type") or "LANDING_PAGE"
    sol = CATALOGO_SOLUCOES.get(scope_code) or CATALOGO_SOLUCOES["LANDING_PAGE"]

    msg_cliente = (
        f"Acabei de confirmar aqui com a direção uma condição especial pro projeto da {lead.get('title')}: "
        f"conseguimos fechar a {sol['nome']} por {formatted_offer}, já deixando tudo pronto pra captar clientes no WhatsApp. "
        f"Fica bom assim pra gente já montar o seu protótipo?"
    )

    client_delivery = responder_como_humano(conv["chatid"], msg_cliente, db_path=db_path)
    append_agent_message(
        conversation_id=conv["id"],
        role="model",
        direction="outbound",
        content=msg_cliente,
        external_message_id=client_delivery.get("external_message_id", ""),
        db_path=db_path,
    )

    ack_boss = (
        f"✅ Proposta enviada agora para *{lead.get('title')}* ({conv['chatid']}):\n"
        f"\"{msg_cliente}\""
    )
    send_whatsapp_text(boss_chatid, ack_boss, db_path=db_path)

    return {
        "handled": True,
        "action": "price_forwarded_to_client",
        "conversation_id": conv["id"],
        "approved_price_text": formatted_offer,
        "client_message": msg_cliente,
    }


# ---------------------------------------------------------------------------
# Motor de Resposta Comercial + Guardrail Anti-Fiscal + Fechamento -> Protótipo
# ---------------------------------------------------------------------------


def _specialist_commercial_reply(
    lead: Dict[str, Any],
    conv: Dict[str, Any],
    client_text: str,
    scope_type: str,
    has_fiscal: bool,
    price_info: Optional[Dict[str, Any]] = None,
) -> str:
    title = lead.get("title") or "sua empresa"
    city = lead.get("city") or "sua região"
    sol = CATALOGO_SOLUCOES.get(scope_type) or CATALOGO_SOLUCOES["LANDING_PAGE"]

    if has_fiscal:
        return (
            f"A parte de emissão de nota fiscal e impostos nós não fazemos pra não assumir responsabilidade tributária, "
            f"mas toda a parte comercial, captação de clientes e {sol['nome'].lower()} a gente entrega redonda. "
            f"Hoje o foco maior da {title} é receber mais clientes no WhatsApp ou organizar agendamentos e pedidos?"
        )

    if price_info:
        faixa = price_info["price_range"]
        return (
            f"Para o padrão da {title}, uma {sol['nome']} costuma ficar na faixa de {faixa} dependendo dos recursos que incluirmos. "
            f"Já acionei meu sócio aqui pra liberar uma condição especial fechada pro caso de vocês, você prefere focar só na captação pro WhatsApp ou incluir catálogo e agendamento?"
        )

    if scope_type == "SISTEMA_SOB_MEDIDA":
        return (
            f"Perfeito, além da página de alta conversão a gente consegue montar esse painel comercial sob medida pra {title} "
            f"organizar os atendimentos e pedidos sem complicação (sem parte fiscal). "
            f"Quais são as 2 principais funções que mais ajudariam seu dia a dia hoje?"
        )

    if re.search(r"\b(instagram|insta|rede\s+social|j[aá]\s+tenho)\b", client_text or "", re.IGNORECASE):
        return (
            f"O Instagram ajuda muito com quem já conhece a {title}, mas quem pesquisa pelo serviço no Google em {city} "
            f"com intenção imediata de compra precisa cair numa Landing Page rápida que já leva direto pro seu WhatsApp. "
            f"Hoje qual é o serviço carro-chefe que vocês mais querem vender?"
        )

    return (
        f"A ideia pro caso da {title} em {city} é colocar no ar uma {sol['nome']} pensada pra {sol['resultado']}. "
        f"Qual é o principal serviço ou diferencial de vocês hoje pra destacarmos logo no topo da página?"
    )


def generate_agent_reply(
    conv: Dict[str, Any],
    lead: Dict[str, Any],
    client_text: str,
    sender_name: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executa um turno completo de raciocínio comercial do agente para o cliente:
    1. Verifica trava anti-fiscal obrigatória.
    2. Verifica fechamento de negócio -> aciona fábrica de protótipo por IA e avisa o Chefe (+551999958516).
    3. Verifica pedido de preço -> informa faixa de referência e dispara consulta ao Chefe (+551999958516).
    4. Consulta LLM (`chave.env`) com fallback imediato para o motor especialista.
    """
    settings = get_agent_settings(db_path)
    reqs = dict(conv.get("collected_requirements") or {})
    current_scope = reqs.get("scope_code") or (
        "SISTEMA_SOB_MEDIDA"
        if lead.get("recommended_service") == "SISTEMA_COMPLEXO"
        else "LANDING_PAGE"
    )
    scope_type = detect_scope_from_text(client_text, current_scope)
    reqs["scope_code"] = scope_type
    reqs["ultima_fala_cliente"] = client_text.strip()
    if sender_name:
        reqs["nome_contato"] = sender_name.strip()

    has_fiscal = detect_fiscal_request(client_text)
    if has_fiscal:
        reqs["restricao_fiscal_informada"] = True

    update_agent_conversation(
        conversation_id=conv["id"],
        collected_requirements=reqs,
        db_path=db_path,
    )

    # 1. Cliente fechou negócio ou pediu para montar o protótipo (sem escopo fiscal bloqueante pendente)
    if CLOSE_DEAL_REGEX.search(client_text or "") and not has_fiscal:
        update_agent_conversation(
            conversation_id=conv["id"],
            status="closed_won",
            collected_requirements={"fechamento_confirmado": True, "pedido_final": client_text.strip()},
            db_path=db_path,
        )
        update_lead_management(lead["id"], lead_status="fechado", db_path=db_path)

        from app.services.prototype_generator import generate_prototype_for_lead

        proto = generate_prototype_for_lead(
            lead_id=lead["id"],
            conversation_id=conv["id"],
            custom_instructions=client_text.strip(),
            scope_override=scope_type,
            notify_boss=True,
            db_path=db_path,
        )

        reply = (
            f"Fechado! Já coloquei nossa inteligência pra montar o protótipo da {lead.get('title')} com base no que combinamos "
            f"e meu sócio já entra aqui com você em instantes pra te mostrar e alinhar os detalhes finais."
        )
        return {
            "reply": reply,
            "action": "deal_closed_prototype_generated",
            "prototype": proto,
            "scope_type": scope_type,
        }

    # 2. Cliente perguntou preço / orçamento / valores -> informa faixa e consulta Chefe (+551999958516)
    price_info = None
    if PRICE_INQUIRY_REGEX.search(client_text or ""):
        price_info = trigger_boss_price_consultation(
            conv=conv,
            lead=lead,
            client_text=client_text,
            scope_type=scope_type,
            db_path=db_path,
        )

    # 3. Se houve pedido fiscal ou consulta de preço, usamos resposta controlada com guardrail
    if has_fiscal or price_info:
        reply_text = _specialist_commercial_reply(
            lead=lead,
            conv=conv,
            client_text=client_text,
            scope_type=scope_type,
            has_fiscal=has_fiscal,
            price_info=price_info,
        )
        return {
            "reply": limpar_texto_whatsapp(reply_text),
            "action": "fiscal_guardrail" if has_fiscal else "price_consulted_boss",
            "price_consultation": price_info["consultation"] if price_info else None,
            "scope_type": scope_type,
        }

    # 4. Conversa consultiva via LLM (chave.env) + fallback especialista
    history_rows = list_agent_messages(conv["id"], limit=20, db_path=db_path)
    llm_messages: List[Dict[str, str]] = []
    for h in history_rows:
        if h["role"] in ("user", "model"):
            llm_messages.append({"role": h["role"], "content": h["content"]})
    if not llm_messages or llm_messages[-1]["content"] != client_text:
        llm_messages.append({"role": "user", "content": client_text})

    sys_prompt = build_agent_system_prompt(lead, conv, settings)
    llm_reply, provider = call_llm_chat(sys_prompt, llm_messages, temperature=0.4, max_tokens=220)

    if llm_reply:
        cleaned = limpar_texto_whatsapp(llm_reply)
        # Guardrail mecânico pós-LLM: se o modelo mencionar nota fiscal sem negar, substitui pelo especialista
        if detect_fiscal_request(cleaned) and "não fazemos" not in cleaned.lower() and "nao fazemos" not in cleaned.lower():
            cleaned = _specialist_commercial_reply(lead, conv, client_text, scope_type, True, None)
        return {
            "reply": cleaned,
            "action": "negotiation_turn",
            "provider": provider,
            "scope_type": scope_type,
        }

    fallback_reply = _specialist_commercial_reply(
        lead=lead,
        conv=conv,
        client_text=client_text,
        scope_type=scope_type,
        has_fiscal=False,
        price_info=None,
    )
    return {
        "reply": limpar_texto_whatsapp(fallback_reply),
        "action": "negotiation_turn",
        "provider": "specialist_engine",
        "scope_type": scope_type,
    }


def process_conversation_turn(
    chatid: str,
    text: str,
    message_ids: Optional[List[str]] = None,
    sender_name: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executa o turno de uma conversa com todas as proteções de `agente-barbearia`:
    - Localiza a conversa ativa pelo `chatid`
    - Marca o histórico antes de pensar (`max_msg_id` e `turn_version`)
    - Checa DEPOIS do modelo se o humano assumiu ou se chegou mensagem nova (Cicatriz #3: anti-resposta-velha)
    - Envia com `responder_como_humano`
    """
    conv = get_active_conversation_by_chatid(chatid, db_path=db_path)
    if not conv:
        return {"ok": False, "ignored": True, "reason": "no_authorized_conversation_for_chatid"}

    if is_conversation_paused(conv, db_path=db_path):
        return {"ok": False, "ignored": True, "reason": "conversation_paused_by_human"}

    lead = get_lead(conv["lead_id"], db_path=db_path)
    if not lead:
        return {"ok": False, "ignored": True, "reason": "lead_not_found"}

    turn_before = int(conv.get("turn_version", 0))
    inbound_msg_id = append_agent_message(
        conversation_id=conv["id"],
        role="user",
        direction="inbound",
        content=text,
        external_message_id=(message_ids or [""])[0],
        db_path=db_path,
    )

    # Atualiza status do lead para 'respondeu' se estava 'contatado'
    if lead.get("lead_status") in ("novo", "analisado", "contatado"):
        update_lead_management(lead["id"], lead_status="respondeu", db_path=db_path)

    result = generate_agent_reply(
        conv=conv,
        lead=lead,
        client_text=text,
        sender_name=sender_name,
        db_path=db_path,
    )

    # Cicatriz #3: Revalida estado DEPOIS que o modelo pensou
    conv_after = get_agent_conversation(conv["id"], db_path=db_path) or {}
    if is_conversation_paused(conv_after, db_path=db_path):
        delete_agent_messages_after(conv["id"], inbound_msg_id - 1, db_path=db_path)
        return {"ok": False, "ignored": True, "reason": "human_assumed_during_generation"}

    with _BUFFER_LOCK:
        has_newer_buffer = bool(_BUFFERS.get(normalize_phone_digits(chatid)))
    if has_newer_buffer or int(conv_after.get("turn_version", 0)) != turn_before:
        delete_agent_messages_after(conv["id"], inbound_msg_id, db_path=db_path)
        return {"ok": False, "ignored": True, "reason": "stale_reply_client_sent_more"}

    reply_text = result["reply"]
    delivery = responder_como_humano(conv["chatid"], reply_text, ids_recebidos=message_ids, db_path=db_path)
    append_agent_message(
        conversation_id=conv["id"],
        role="model",
        direction="outbound",
        content=reply_text,
        external_message_id=delivery.get("external_message_id", ""),
        db_path=db_path,
    )

    return {
        "ok": True,
        "conversation_id": conv["id"],
        "lead_id": lead["id"],
        "reply": reply_text,
        "action": result.get("action"),
        "price_consultation": result.get("price_consultation"),
        "prototype": result.get("prototype"),
        "delivery": delivery,
    }


def _flush_buffer(chatid_clean: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with _BUFFER_LOCK:
        buf = _BUFFERS.pop(chatid_clean, None)
    if not buf:
        return None
    timer = buf.get("timer")
    if timer:
        timer.cancel()
    combined_text = "\n".join(buf["parts"])
    return process_conversation_turn(
        chatid=chatid_clean,
        text=combined_text,
        message_ids=buf["ids"],
        sender_name=buf.get("sender_name"),
        db_path=db_path,
    )


def process_incoming_webhook(
    payload: Dict[str, Any],
    immediate: bool = False,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Pipeline de entrada do Webhook (UAZAPI / Micro-Bridge QR Code):
    Segue exatamente a ordem de filtros de `agente-barbearia/src/index.ts`.
    """
    msg = payload.get("message") if isinstance(payload.get("message"), dict) else payload
    if not isinstance(msg, dict):
        return {"ok": False, "ignored": True, "reason": "empty_message"}

    # 1. Grupo? Sai.
    if msg.get("isGroup") is True:
        return {"ok": False, "ignored": True, "reason": "group_message"}

    # 2. Cicatriz #1: Sempre usar `chatid`, nunca `sender` (@lid)
    raw_chatid = (msg.get("chatid") or "").strip()
    if not raw_chatid or "@lid" in raw_chatid:
        return {"ok": False, "ignored": True, "reason": "invalid_or_lid_chatid"}

    chatid_clean = normalize_phone_digits(raw_chatid)
    if not chatid_clean:
        return {"ok": False, "ignored": True, "reason": "empty_chatid_digits"}

    settings = get_agent_settings(db_path)

    # 3. Mensagem enviada pelo próprio número do negócio (`fromMe === true`)
    if msg.get("fromMe") is True:
        # Se NÃO foi enviada pela API (`wasSentByApi !== true`), o humano digitou pelo celular! (Handoff 90%)
        if msg.get("wasSentByApi") is not True:
            conv = get_active_conversation_by_chatid(chatid_clean, db_path=db_path)
            if conv:
                with _BUFFER_LOCK:
                    existing_buf = _BUFFERS.pop(chatid_clean, None)
                    if existing_buf and existing_buf.get("timer"):
                        existing_buf["timer"].cancel()
                pause_min = int(settings.get("pause_minutes_on_human") or 60)
                pause_conversation(
                    conv["id"],
                    minutes=pause_min,
                    reason="humano_digitou_no_whatsapp",
                    db_path=db_path,
                )
                return {
                    "ok": True,
                    "handoff": True,
                    "conversation_id": conv["id"],
                    "paused_minutes": pause_min,
                }
        return {"ok": True, "ignored": True, "reason": "from_me_api"}

    # 4. Tipo diferente de texto? Sai.
    msg_type = (msg.get("type") or "text").lower()
    if msg_type != "text":
        return {"ok": False, "ignored": True, "reason": f"non_text_type:{msg_type}"}

    texto = (msg.get("text") or "").strip()
    if not texto:
        return {"ok": False, "ignored": True, "reason": "empty_text"}

    # 5. A mensagem veio do número do Chefe (+551999958516)?
    boss_phone = settings.get("boss_phone") or "551999958516"
    if phones_match_br(chatid_clean, boss_phone):
        boss_res = handle_boss_incoming_message(chatid_clean, texto, db_path=db_path)
        return {"ok": True, "from_boss": True, **boss_res}

    # 6. Conversa pausada porque o humano assumiu?
    conv = get_active_conversation_by_chatid(chatid_clean, db_path=db_path)
    if not conv:
        return {"ok": False, "ignored": True, "reason": "no_authorized_conversation"}
    if is_conversation_paused(conv, db_path=db_path):
        return {"ok": False, "ignored": True, "reason": "conversation_paused_by_human"}

    # 7. Agrupamento (Debounce Cicatriz #2) ou execução imediata
    debounce_sec = 0.0 if immediate else float(settings.get("debounce_seconds") or 0.0)
    msg_id = str(msg.get("messageid") or "")
    sender_name = msg.get("senderName")

    if debounce_sec <= 0.05:
        return process_conversation_turn(
            chatid=chatid_clean,
            text=texto,
            message_ids=[msg_id] if msg_id else [],
            sender_name=sender_name,
            db_path=db_path,
        )

    with _BUFFER_LOCK:
        existing = _BUFFERS.get(chatid_clean)
        if existing:
            existing["parts"].append(texto)
            if msg_id:
                existing["ids"].append(msg_id)
            if sender_name:
                existing["sender_name"] = sender_name
            if existing.get("timer"):
                existing["timer"].cancel()
            t = threading.Timer(debounce_sec, _flush_buffer, args=(chatid_clean, db_path))
            t.daemon = True
            existing["timer"] = t
            t.start()
        else:
            t = threading.Timer(debounce_sec, _flush_buffer, args=(chatid_clean, db_path))
            t.daemon = True
            _BUFFERS[chatid_clean] = {
                "parts": [texto],
                "ids": [msg_id] if msg_id else [],
                "sender_name": sender_name,
                "timer": t,
            }
            t.start()

    return {
        "ok": True,
        "buffered": True,
        "chatid": chatid_clean,
        "debounce_seconds": debounce_sec,
    }
