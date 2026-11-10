import html
import json
import os
import re
from typing import Any, Dict, List, Optional

from app.database import (
    get_agent_conversation,
    get_agent_settings,
    get_lead,
    list_agent_messages,
    normalize_phone_digits,
    save_lead_prototype,
)
from app.services.ai_provider import call_llm_chat
from app.services.whatsapp_agent import FISCAL_KEYWORDS_REGEX, send_whatsapp_text

PROTOTYPES_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "exports",
    "prototipos",
)


def _sanitize_non_fiscal_requirements(text: str) -> str:
    if not text:
        return ""
    cleaned = FISCAL_KEYWORDS_REGEX.sub("[escopo comercial sem módulo fiscal]", text)
    return cleaned.strip()


def build_prototype_briefing(
    lead: Dict[str, Any],
    conv: Optional[Dict[str, Any]] = None,
    custom_instructions: Optional[str] = None,
    scope_override: Optional[str] = None,
) -> Dict[str, Any]:
    reqs = (conv or {}).get("collected_requirements") or {}
    scope_type = (
        scope_override
        or reqs.get("scope_code")
        or ("SISTEMA_SOB_MEDIDA" if lead.get("recommended_service") == "SISTEMA_COMPLEXO" else "LANDING_PAGE")
    )

    chat_requests: List[str] = []
    if conv and conv.get("id"):
        msgs = list_agent_messages(int(conv["id"]), limit=30)
        for m in msgs:
            if m.get("role") == "user" and m.get("content"):
                chat_requests.append(_sanitize_non_fiscal_requirements(m["content"]))

    if custom_instructions:
        chat_requests.append(_sanitize_non_fiscal_requirements(custom_instructions))

    return {
        "lead_id": lead.get("id"),
        "business_name": lead.get("title") or "Empresa Local",
        "category": lead.get("category") or lead.get("niche_slug") or "Serviços Especializados",
        "city": lead.get("city") or "Sua Cidade",
        "state": lead.get("state") or "SP",
        "phone": lead.get("phone") or lead.get("whatsapp_clean") or "",
        "whatsapp_clean": normalize_phone_digits(lead.get("whatsapp_clean") or lead.get("phone") or ""),
        "address": lead.get("address") or "",
        "review_rating": float(lead.get("review_rating") or 4.9),
        "review_count": int(lead.get("review_count") or 48),
        "suggested_domain": lead.get("suggested_domain") or "",
        "primary_pain": lead.get("primary_pain") or "SEM_SITE",
        "pain_summary": lead.get("pain_summary") or "",
        "scope_type": scope_type,
        "approved_price_text": (conv or {}).get("approved_price_text") or "",
        "client_requests": chat_requests,
        "fiscal_policy": "PROIBIDO incluir qualquer módulo fiscal (NF-e/NFC-e/impostos). Foco 100% comercial e operacional.",
    }


def _build_specialist_html_prototype(briefing: Dict[str, Any]) -> str:
    name = html.escape(str(briefing.get("business_name") or "Empresa"))
    category = html.escape(str(briefing.get("category") or "Atendimento Especializado"))
    city = html.escape(str(briefing.get("city") or "Sua Região"))
    address = html.escape(str(briefing.get("address") or f"Atendimento em {city}"))
    rating = float(briefing.get("review_rating") or 4.9)
    rating_fmt = f"{rating:.1f}" if rating > 0 else "4.9"
    reviews = int(briefing.get("review_count") or 52)
    wa_digits = briefing.get("whatsapp_clean") or "5519999999999"
    domain = html.escape(str(briefing.get("suggested_domain") or ""))
    scope_type = str(briefing.get("scope_type") or "LANDING_PAGE")
    reqs_list = briefing.get("client_requests") or []
    reqs_summary = html.escape(" | ".join(reqs_list[-3:])) if reqs_list else "Captação rápida via WhatsApp e apresentação de autoridade"

    is_system = scope_type == "SISTEMA_SOB_MEDIDA"
    badge_label = "Sistema Comercial & Agendamento Online" if is_system else f"Referência em {city}"

    system_module_html = ""
    if is_system:
        system_module_html = f"""
        <section id="agendamento" class="py-16 bg-slate-900 text-white">
          <div class="max-w-6xl mx-auto px-6">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
              <div>
                <span class="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  MÓDULO OPERACIONAL INTERATIVO (SEM ESCOPO FISCAL)
                </span>
                <h2 class="text-3xl font-bold mt-3">Simulador de Agendamento & Painel de Pedidos</h2>
                <p class="text-slate-400 mt-1">Fluxo integrado para o cliente escolher horário/serviço e cair pronto no WhatsApp da {name}.</p>
              </div>
            </div>
            <div class="grid md:grid-cols-2 gap-8">
              <div class="bg-slate-800/90 border border-slate-700 rounded-2xl p-6 shadow-xl">
                <h3 class="text-lg font-semibold mb-4 text-emerald-400">1. Visão do Cliente (Auto-Agendamento)</h3>
                <div class="space-y-4">
                  <div>
                    <label class="block text-xs text-slate-300 mb-1">Nome do Cliente</label>
                    <input id="sim-nome" type="text" placeholder="Ex: Marcos Silva" class="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700 text-white"/>
                  </div>
                  <div>
                    <label class="block text-xs text-slate-300 mb-1">Serviço Desejado</label>
                    <select id="sim-servico" class="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700 text-white">
                      <option value="Atendimento Principal">Atendimento Principal ({category})</option>
                      <option value="Pacote Completo Premium">Pacote Completo Premium</option>
                      <option value="Avaliação / Orçamento Rápido">Avaliação / Orçamento Rápido</option>
                    </select>
                  </div>
                  <div class="grid grid-cols-2 gap-3">
                    <div>
                      <label class="block text-xs text-slate-300 mb-1">Dia Preferido</label>
                      <input id="sim-data" type="date" class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"/>
                    </div>
                    <div>
                      <label class="block text-xs text-slate-300 mb-1">Período</label>
                      <select id="sim-periodo" class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white">
                        <option>Manhã (09h - 12h)</option>
                        <option>Tarde (14h - 18h)</option>
                      </select>
                    </div>
                  </div>
                  <button onclick="simularReserva()" class="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition">
                    Testar Agendamento Instantâneo
                  </button>
                </div>
              </div>
              <div class="bg-slate-800/90 border border-slate-700 rounded-2xl p-6 shadow-xl">
                <h3 class="text-lg font-semibold mb-4 text-sky-400">2. Visão do Painel da {name}</h3>
                <div id="painel-reservas" class="space-y-3 text-sm">
                  <div class="p-3.5 rounded-xl bg-slate-900/90 border border-slate-700 flex justify-between items-center">
                    <div>
                      <div class="font-semibold text-white">Cliente Exemplo #1</div>
                      <div class="text-xs text-slate-400">Atendimento Principal • Hoje às 15:00</div>
                    </div>
                    <span class="px-2.5 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-300 font-medium">Confirmado via WhatsApp</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{name} — {category} em {city}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans antialiased">
  <!-- Barra de Aviso do Protótipo Gerado por IA -->
  <div class="bg-emerald-950/90 border-b border-emerald-500/30 px-4 py-2 text-xs text-emerald-200 flex flex-wrap justify-between items-center gap-2">
    <div>
      <strong>PROTÓTIPO IA PERSONALIZADO:</strong> {name} ({city}) • Escopo: <strong>{html.escape(scope_type)}</strong>
      {f'• Domínio sugerido: <u>{domain}</u>' if domain else ''}
    </div>
    <div class="text-emerald-300">Solicitações aplicadas: {reqs_summary}</div>
  </div>

  <!-- Header -->
  <header class="sticky top-0 z-30 backdrop-blur bg-slate-950/85 border-b border-slate-800">
    <div class="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
      <div>
        <span class="text-xl font-extrabold tracking-tight text-white">{name}</span>
        <span class="hidden sm:inline-block ml-3 text-xs text-slate-400">{category} • {city}</span>
      </div>
      <a href="https://wa.me/{wa_digits}?text=Ol%C3%A1%2C%20vim%20pelo%20site%20da%20{html.escape(name)}%20e%20gostaria%20de%20um%20atendimento!"
         target="_blank"
         class="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition shadow-lg shadow-emerald-500/20">
        Chamar no WhatsApp
      </a>
    </div>
  </header>

  <!-- Hero Section -->
  <section class="relative overflow-hidden py-20 md:py-28 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950">
    <div class="max-w-6xl mx-auto px-6 grid md:grid-cols-12 gap-10 items-center">
      <div class="md:col-span-7 space-y-6">
        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
          <span>★ {rating_fmt} no Google ({reviews}+ avaliações)</span>
          <span>•</span>
          <span>{badge_label}</span>
        </div>
        <h1 class="text-4xl md:text-5xl font-extrabold leading-tight text-white">
          A melhor experiência em <span class="text-emerald-400">{category}</span> em {city} com atendimento imediato.
        </h1>
        <p class="text-lg text-slate-300 leading-relaxed">
          Na <strong>{name}</strong> você encontra qualidade comprovada, agilidade no atendimento direto pelo WhatsApp e soluções sob medida para o que você precisa hoje.
        </p>
        <div class="flex flex-wrap gap-4 pt-2">
          <a href="https://wa.me/{wa_digits}?text=Ol%C3%A1%21%20Quero%20agendar%20ou%20pedir%20or%C3%A7amento%20na%20{html.escape(name)}"
             target="_blank"
             class="px-7 py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold text-base shadow-xl shadow-emerald-500/25 transition">
            Falar Agora no WhatsApp →
          </a>
          <a href="#diferenciais"
             class="px-6 py-4 rounded-2xl border border-slate-700 hover:border-slate-500 text-slate-200 font-semibold text-base transition">
            Ver Diferenciais e Serviços
          </a>
        </div>
      </div>
      <div class="md:col-span-5">
        <div class="bg-slate-900/90 border border-slate-800 p-7 rounded-3xl shadow-2xl space-y-5">
          <div class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <div class="text-xs uppercase tracking-wider text-emerald-400 font-bold">Atendimento Rápido</div>
              <div class="text-lg font-bold text-white mt-0.5">{name}</div>
            </div>
            <span class="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold">Online Agora</span>
          </div>
          <ul class="space-y-3 text-sm text-slate-300">
            <li class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">✓</span>
              Orçamento e confirmação em minutos pelo celular
            </li>
            <li class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">✓</span>
              Equipe especialista altamente avaliada em {city}
            </li>
            <li class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">✓</span>
              Localização de fácil acesso: {address}
            </li>
          </ul>
          <a href="https://wa.me/{wa_digits}" target="_blank"
             class="block text-center w-full py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-400 font-bold text-sm border border-slate-700 transition">
            Solicitar Atendimento Prioritário
          </a>
        </div>
      </div>
    </div>
  </section>

  {system_module_html}

  <!-- Diferenciais -->
  <section id="diferenciais" class="py-16 bg-slate-950 border-t border-slate-900">
    <div class="max-w-6xl mx-auto px-6">
      <h2 class="text-3xl font-bold text-white text-center mb-12">Por que escolher a {name}?</h2>
      <div class="grid md:grid-cols-3 gap-6">
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <div class="text-emerald-400 font-bold text-lg mb-2">1. Agilidade no WhatsApp</div>
          <p class="text-slate-400 text-sm">Sem burocracia ou formulários lentos: você clica e já fala direto com nossa equipe para resolver o que precisa.</p>
        </div>
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <div class="text-emerald-400 font-bold text-lg mb-2">2. Confiança Comprovada</div>
          <p class="text-slate-400 text-sm">Avaliação média de {rating_fmt} estrelas pelos clientes de {city}, garantindo segurança do início ao fim.</p>
        </div>
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <div class="text-emerald-400 font-bold text-lg mb-2">3. Atendimento Sob Medida</div>
          <p class="text-slate-400 text-sm">Estrutura preparada para atender com hora marcada e total transparência comercial.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="py-10 bg-slate-950 border-t border-slate-900 text-center text-xs text-slate-500">
    <div class="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row justify-between items-center gap-4">
      <div>© {name} — {city}. Todos os direitos reservados.</div>
      <div>Localização: {address}</div>
    </div>
  </footer>

  <script>
    function simularReserva() {{
      var nome = document.getElementById('sim-nome') ? document.getElementById('sim-nome').value || 'Novo Cliente' : 'Novo Cliente';
      var servico = document.getElementById('sim-servico') ? document.getElementById('sim-servico').value : 'Atendimento';
      var data = document.getElementById('sim-data') ? document.getElementById('sim-data').value || 'Próximo horário' : 'Próximo horário';
      var periodo = document.getElementById('sim-periodo') ? document.getElementById('sim-periodo').value : '';
      var painel = document.getElementById('painel-reservas');
      if (painel) {{
        var card = document.createElement('div');
        card.className = 'p-3.5 rounded-xl bg-slate-900/90 border border-emerald-500/40 flex justify-between items-center';
        card.innerHTML = '<div><div class="font-semibold text-white">' + nome + '</div><div class="text-xs text-slate-400">' + servico + ' • ' + data + ' (' + periodo + ')</div></div><span class="px-2.5 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-300 font-medium">Novo no Painel</span>';
        painel.prepend(card);
      }}
    }}
  </script>
</body>
</html>"""


def generate_prototype_for_lead(
    lead_id: int,
    conversation_id: Optional[int] = None,
    custom_instructions: Optional[str] = None,
    scope_override: Optional[str] = None,
    notify_boss: bool = True,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Gera o protótipo navegável completo (LP ou Sistema Web sem escopo fiscal) para o lead:
    1. Monta o briefing com dados do Raio-X + solicitações da conversa no WhatsApp.
    2. Tenta sintetizar via IA configurada em `C:\\Projetos Soft\\Painel\\chave.env` (OpenRouter / NVIDIA / Gemini),
       com fallback imediato para o construtor especialista responsivo.
    3. Salva o HTML em `exports/prototipos/lead_<id>/index.html` e no banco SQLite (`lead_prototypes`).
    4. Envia aviso imediato para o Chefe no `+551999958516` para revisão antes de mandar ao cliente.
    """
    lead = get_lead(lead_id, db_path=db_path)
    if not lead:
        raise ValueError(f"Lead #{lead_id} não encontrado para geração de protótipo")

    conv = get_agent_conversation(conversation_id, db_path=db_path) if conversation_id else None
    briefing = build_prototype_briefing(
        lead=lead,
        conv=conv,
        custom_instructions=custom_instructions,
        scope_override=scope_override,
    )

    sys_prompt = (
        "Você é um Web Designer e Engenheiro Front-end Sênior especialista em páginas de alta conversão. "
        "Retorne APENAS um documento HTML5 completo (começando com <!DOCTYPE html> e usando TailwindCSS via CDN) "
        "para a empresa descrita no briefing. Nunca inclua recursos fiscais/tributários (NF-e/NFC-e/impostos)."
    )
    user_prompt = f"Crie o HTML5 completo e responsivo para este briefing:\n{json.dumps(briefing, ensure_ascii=False)}"

    llm_html, provider_used = call_llm_chat(
        system_prompt=sys_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.3,
        max_tokens=1800,
        timeout_sec=8.0,
    )

    if llm_html and "<html" in llm_html.lower() and "</html>" in llm_html.lower():
        # Extrai bloco HTML caso venha cercado por ```html
        m = re.search(r"(<!DOCTYPE html>.*?</html>|<html.*?</html>)", llm_html, flags=re.IGNORECASE | re.DOTALL)
        html_content = m.group(1) if m else llm_html
    else:
        html_content = _build_specialist_html_prototype(briefing)
        provider_used = f"{provider_used}+template_alta_conversao"

    slug = re.sub(r"[^a-z0-9]+", "-", (lead.get("title") or "empresa").lower()).strip("-") or f"lead-{lead_id}"
    lead_dir = os.path.join(PROTOTYPES_BASE_DIR, f"lead_{lead_id}_{slug}")
    os.makedirs(lead_dir, exist_ok=True)

    html_path = os.path.join(lead_dir, "index.html")
    briefing_path = os.path.join(lead_dir, "briefing.json")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(briefing_path, "w", encoding="utf-8") as f:
        json.dump(briefing, f, ensure_ascii=False, indent=2)

    saved = save_lead_prototype(
        lead_id=lead_id,
        conversation_id=conversation_id,
        scope_type=briefing["scope_type"],
        briefing=briefing,
        html_content=html_content,
        output_path=html_path,
        ai_provider_used=provider_used,
        status="ready",
        db_path=db_path,
    )

    preview_url = f"/api/agent/prototypes/{lead_id}/preview"
    saved["preview_url"] = preview_url

    if notify_boss:
        settings = get_agent_settings(db_path)
        boss_phone = normalize_phone_digits(settings.get("boss_phone") or "551999958516")
        msg_boss = (
            f"🚀 *[Protótipo IA Pronto - {lead.get('title')} ({lead.get('city')})]*\n"
            f"• *Escopo*: {briefing['scope_type']}\n"
            f"• *Motor*: {provider_used}\n"
            f"• *Preview no Painel*: http://127.0.0.1:8090{preview_url}\n"
            f"• *Arquivo Local*: `{html_path}`\n"
            f"Revise no Painel de Busca antes de enviar para o cliente!"
        )
        send_whatsapp_text(boss_phone, msg_boss, db_path=db_path)

    return saved
