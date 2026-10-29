let ALL_NICHES = [];
let SELECTED_NICHES = new Set([
  "clinicas-odontologicas",
  "escritorios-advocacia",
  "imobiliarias-corretores",
]);
let CURRENT_LEADS = [];

const PAIN_LABELS = {
  SEM_SITE: "Sem Site Próprio",
  DOMINIO_LIVRE: "Só Bio + Domínio Livre",
  SITE_FORA_DO_AR: "Site Fora do Ar",
  OPORTUNIDADE_SISTEMA: "Oportunidade de Sistema",
  SITE_AMADOR_ANTIGO: "Site Antigo / Amador",
};

const SERVICE_LABELS = {
  SITE_NOVO: "Criação de Site / LP",
  REFORMA_SITE: "Reforma de Site",
  SISTEMA_COMPLEXO: "Sistema Mais Complexo",
};

async function initDashboard() {
  await Promise.all([loadHealthAndStats(), loadNiches(), loadLeads()]);
}

async function loadHealthAndStats() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const badge = document.getElementById("engine-badge");
    if (data.scraper_engine && data.scraper_engine.online) {
      badge.textContent = "● Docker Maps Scraper: ONLINE (8080)";
      badge.style.background = "#dcfce7";
      badge.style.color = "#166534";
    } else {
      badge.textContent = "○ Docker Maps Offline (Modo Simulação/CSV Ativo)";
      badge.style.background = "#fef3c7";
      badge.style.color = "#92400e";
    }

    const st = data.stats || {};
    document.getElementById("stat-total").textContent = st.total_leads ?? 0;
    document.getElementById("stat-without-site").textContent = st.without_site ?? 0;
    document.getElementById("stat-domain-free").textContent = st.domain_available ?? 0;
    document.getElementById("stat-site-down").textContent = st.site_down ?? 0;
    document.getElementById("stat-complex").textContent = st.complex_system_opportunities ?? 0;
    document.getElementById("stat-owners").textContent = `${st.assigned_eu ?? 0} / ${st.assigned_amigo ?? 0}`;
    document.getElementById("stat-queue").textContent = st.outreach_queue_ready ?? 0;
    document.getElementById("btn-queue-count").textContent = st.outreach_queue_ready ?? 0;
  } catch (err) {
    console.error("Erro ao carregar health:", err);
  }
}

async function loadNiches() {
  const res = await fetch("/api/niches");
  ALL_NICHES = await res.json();
  renderNichesGrid();
}

function renderNichesGrid() {
  const grid = document.getElementById("niches-grid");
  grid.innerHTML = ALL_NICHES.map((n) => {
    const isSel = SELECTED_NICHES.has(n.slug);
    const offerLabel = SERVICE_LABELS[n.recommended_service || n.recommended_offer] || n.recommended_offer;
    return `
      <div class="niche-chip ${isSel ? "selected" : ""}" onclick="toggleNiche('${n.slug}')">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
          <strong style="font-size:0.9rem;">${isSel ? "☑" : "☐"} ${n.name}</strong>
          <span style="font-size:0.7rem; background:#e5e7eb; padding:2px 6px; border-radius:4px; font-weight:700;">
            ${offerLabel}
          </span>
        </div>
        <div style="font-size:0.78rem; color:var(--text-muted);">${n.description}</div>
        <div style="font-size:0.72rem; color:var(--brand-blue); font-weight:600;">
          CNAE: ${(n.cnae_codes || []).join(", ")}
        </div>
      </div>
    `;
  }).join("");
}

function toggleNiche(slug) {
  if (SELECTED_NICHES.has(slug)) {
    SELECTED_NICHES.delete(slug);
  } else {
    SELECTED_NICHES.add(slug);
  }
  renderNichesGrid();
}

function selectAllNiches(selectAll) {
  if (selectAll) {
    ALL_NICHES.forEach((n) => SELECTED_NICHES.add(n.slug));
  } else {
    SELECTED_NICHES.clear();
  }
  renderNichesGrid();
}

async function runSearchJob() {
  const city = document.getElementById("input-city").value.trim() || "Campinas";
  const state = document.getElementById("input-state").value.trim() || "SP";
  const customKw = document.getElementById("input-custom-kw").value.trim();
  const sourceMode = document.getElementById("input-source-mode").value;
  const depth = parseInt(document.getElementById("input-depth").value || "5", 10);
  const slugs = Array.from(SELECTED_NICHES);

  if (slugs.length === 0 && !customKw) {
    alert("Selecione pelo menos 1 nicho (ou digite um termo extra) antes de rodar a busca!");
    return;
  }

  const btn = document.getElementById("btn-run-job");
  const fb = document.getElementById("job-feedback");
  btn.disabled = true;
  btn.textContent = "Executando Raio-X...";
  fb.textContent = `Buscando empresas em ${city}-${state} e passando pelo motor de Raio-X das 8 ferramentas...`;

  try {
    const res = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        city,
        state,
        niche_slugs: slugs,
        custom_keywords: customKw ? [customKw] : [],
        depth,
        grid_size: 1,
        include_socials: true,
        run_xray: true,
        source_mode: sourceMode,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Erro ao rodar job");
    }
    fb.innerHTML = `<strong style="color:var(--emerald);">✓ Busca concluída!</strong> ${data.total_leads_processed} leads qualificados com Raio-X e scripts prontos.`;
    await Promise.all([loadHealthAndStats(), loadLeads()]);
  } catch (err) {
    fb.innerHTML = `<strong style="color:var(--crimson);">✗ Erro:</strong> ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Buscar & Rodar Raio-X";
  }
}

async function loadCasaDosDadosFilters() {
  const city = document.getElementById("input-city").value.trim() || "Campinas";
  const state = document.getElementById("input-state").value.trim() || "SP";
  const slugs = Array.from(SELECTED_NICHES).join(",");
  const res = await fetch(
    `/api/discovery/casadosdados?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}&niche_slugs=${encodeURIComponent(slugs)}`
  );
  const items = await res.json();
  const box = document.getElementById("casadosdados-box");
  box.style.display = "block";
  box.innerHTML = items
    .map(
      (it) => `
      <div style="padding:6px 0; border-top:1px dashed var(--border-warm);">
        <strong>${it.niche_name}</strong> — CNAE: <code>${(it.cnae_codes || []).join(", ")}</code>
        <a href="${it.search_url}" target="_blank" style="margin-left:8px; color:var(--brand-blue); font-weight:700;">Abrir Pesquisa ↗</a>
      </div>`
    )
    .join("");
}

async function checkQuickDomain() {
  const input = document.getElementById("quick-domain-input").value.trim();
  const out = document.getElementById("quick-domain-result");
  if (!input) return;
  out.textContent = "Consultando RDAP Registro.br...";
  try {
    const res = await fetch(`/api/discovery/registro-br?domain=${encodeURIComponent(input)}`);
    const data = await res.json();
    if (data.available) {
      out.style.color = "var(--emerald)";
      out.innerHTML = `✓ ${data.domain} está LIVRE para registro! <a href="${data.registro_br_url}" target="_blank" style="color:var(--brand-blue);">Registrar ↗</a>`;
    } else {
      out.style.color = "var(--amber)";
      out.innerHTML = `● ${data.domain} já está registrado. <a href="${data.registro_br_url}" target="_blank" style="color:var(--brand-blue);">Ver WHOIS ↗</a>`;
    }
  } catch (e) {
    out.textContent = "Erro ao consultar domínio.";
  }
}

async function loadLeads() {
  const pain = document.getElementById("filter-pain").value;
  const service = document.getElementById("filter-service").value;
  const owner = document.getElementById("filter-owner").value;
  const status = document.getElementById("filter-status").value;
  const search = document.getElementById("filter-search").value.trim();
  const domFree = document.getElementById("filter-domain-free").checked;

  const params = new URLSearchParams();
  if (pain) params.set("primary_pain", pain);
  if (service) params.set("recommended_service", service);
  if (owner) params.set("assigned_to", owner);
  if (status) params.set("lead_status", status);
  if (search) params.set("search_query", search);
  if (domFree) params.set("only_domain_available", "true");

  const res = await fetch(`/api/leads?${params.toString()}`);
  CURRENT_LEADS = await res.json();
  renderLeadsTable();
}

function renderLeadsTable() {
  const tbody = document.getElementById("leads-tbody");
  if (!CURRENT_LEADS.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; padding:32px; color:var(--text-muted);">
          Nenhum lead encontrado para os filtros selecionados. Clique em <strong>Buscar &amp; Rodar Raio-X</strong> acima!
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = CURRENT_LEADS.map((l) => {
    const scoreClass =
      l.opportunity_score >= 85 ? "score-high" : l.opportunity_score >= 70 ? "score-med" : "score-low";
    const painLabel = PAIN_LABELS[l.primary_pain] || l.primary_pain;
    const serviceLabel = SERVICE_LABELS[l.recommended_service] || l.recommended_service;
    const sc = l.outreach_scripts || {};
    const domBadge = l.domain_available_br
      ? `<span style="color:var(--emerald); font-weight:700;">✓ LIVRE: ${l.suggested_domain}</span>`
      : `<span style="color:var(--text-muted);">Registrado (${l.suggested_domain})</span>`;

    return `
      <tr>
        <td><input type="checkbox" class="lead-checkbox" value="${l.id}" /></td>
        <td>
          <span class="badge-score ${scoreClass}">${l.opportunity_score}/100</span>
        </td>
        <td>
          <div style="font-weight:700; font-size:0.95rem;">${l.title}</div>
          <div style="font-size:0.78rem; color:var(--text-muted);">
            ${l.category || l.niche_slug} • ${l.city}-${l.state} • ⭐ ${l.review_rating} (${l.review_count} aval.)
          </div>
          ${l.cnpj ? `<div style="font-size:0.73rem; color:var(--brand-blue);">CNPJ: ${l.cnpj} ${l.opened_date ? `(Abertura: ${l.opened_date})` : ""}</div>` : ""}
        </td>
        <td>
          <div style="margin-bottom:4px;">
            <span class="pain-tag pain-${l.primary_pain}">${painLabel}</span>
            <span style="font-size:0.75rem; font-weight:700; color:var(--text-muted); margin-left:4px;">→ ${serviceLabel}</span>
          </div>
          <div style="font-size:0.8rem; color:var(--text-ink);">${l.pain_summary}</div>
          <div style="font-size:0.74rem; color:var(--text-muted); margin-top:3px;">
            CMS: <strong>${l.detected_cms}</strong>
            ${l.wayback_last_seen ? ` • Web Archive: ${l.wayback_last_seen}` : ""}
          </div>
        </td>
        <td style="font-size:0.82rem;">
          ${domBadge}
          <div style="margin-top:4px;">
            <a href="${(l.external_tools_links || {}).registro_br || "https://registro.br"}" target="_blank" style="font-size:0.75rem; color:var(--brand-blue); font-weight:600;">Verificar no Registro.br ↗</a>
          </div>
        </td>
        <td>
          <div style="display:flex; flex-wrap:wrap; gap:6px;">
            ${
              sc.whatsapp_url
                ? `<a href="${sc.whatsapp_url}" target="_blank" class="btn-whatsapp" onclick="markLeadContacted(${l.id})">WhatsApp 1-Clique ↗</a>`
                : ""
            }
            <button class="btn-secondary" style="padding:6px 10px; font-size:0.78rem;" onclick="openLeadModal(${l.id})">
              Raio-X &amp; Scripts
            </button>
          </div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">
            ${l.phone ? `📞 ${l.phone}` : ""} ${l.emails ? `• ✉️ ${l.emails}` : ""}
          </div>
        </td>
        <td>
          <div style="display:flex; flex-direction:column; gap:6px;">
            <select onchange="updateLeadOwnerOrStatus(${l.id}, {assigned_to: this.value})" style="padding:5px 8px; border:1px solid var(--border-warm); border-radius:6px; font-size:0.78rem;">
              <option value="nao_atribuido" ${l.assigned_to === "nao_atribuido" ? "selected" : ""}>👤 Não atribuído</option>
              <option value="eu" ${l.assigned_to === "eu" ? "selected" : ""}>🙋‍♂️ Eu</option>
              <option value="amigo" ${l.assigned_to === "amigo" ? "selected" : ""}>🤝 Meu Amigo</option>
            </select>
            <select onchange="updateLeadOwnerOrStatus(${l.id}, {lead_status: this.value})" style="padding:5px 8px; border:1px solid var(--border-warm); border-radius:6px; font-size:0.78rem;">
              <option value="novo" ${l.lead_status === "novo" ? "selected" : ""}>Novo</option>
              <option value="analisado" ${l.lead_status === "analisado" ? "selected" : ""}>Analisado</option>
              <option value="contatado" ${l.lead_status === "contatado" ? "selected" : ""}>Contatado</option>
              <option value="respondeu" ${l.lead_status === "respondeu" ? "selected" : ""}>Respondeu</option>
              <option value="reuniao" ${l.lead_status === "reuniao" ? "selected" : ""}>Reunião</option>
              <option value="fechado" ${l.lead_status === "fechado" ? "selected" : ""}>Fechado 💰</option>
              <option value="descartado" ${l.lead_status === "descartado" ? "selected" : ""}>Descartado</option>
            </select>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

async function updateLeadOwnerOrStatus(leadId, patchObj) {
  await fetch(`/api/leads/${leadId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patchObj),
  });
  await loadHealthAndStats();
}

async function markLeadContacted(leadId) {
  await updateLeadOwnerOrStatus(leadId, { lead_status: "contatado" });
  await loadLeads();
}

function toggleSelectAllLeads(checked) {
  document.querySelectorAll(".lead-checkbox").forEach((cb) => {
    cb.checked = checked;
  });
}

async function openLeadModal(leadId) {
  const res = await fetch(`/api/leads/${leadId}`);
  const l = await res.json();
  const sc = l.outreach_scripts || {};
  const ext = l.external_tools_links || {};

  document.getElementById("modal-lead-title").textContent = `${l.title} — Score ${l.opportunity_score}/100`;
  document.getElementById("modal-lead-subtitle").textContent = `${l.address || l.city} • 📞 ${l.phone || "Sem telefone"} • ✉️ ${l.emails || "Sem e-mail"}`;

  document.getElementById("modal-lead-body").innerHTML = `
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(420px, 1fr)); gap:20px;">
      <!-- Coluna Esquerda: Diagnóstico das 8 Ferramentas -->
      <div>
        <div class="section-bar">Diagnóstico das 8 Ferramentas</div>
        <div class="tool-card" style="margin-bottom:12px;">
          <div style="font-weight:700; margin-bottom:6px;">Resumo da Oportunidade (${SERVICE_LABELS[l.recommended_service] || l.recommended_service})</div>
          <div style="font-size:0.9rem; color:var(--text-ink); margin-bottom:10px;">${l.pain_summary}</div>
          <ul style="margin:0; padding-left:18px; font-size:0.84rem; color:var(--text-muted);">
            <li><strong>Website cadastrado:</strong> ${l.website || "Nenhum (Sem site)"}</li>
            <li><strong>Status no Ar (DownForEveryone):</strong> ${l.has_website ? (l.site_in_air ? "No Ar (HTTP " + l.http_status + ")" : "FORA DO AR / Erro") : "Não possui site"}</li>
            <li><strong>Domínio Sugerido (Registro.br):</strong> <code>${l.suggested_domain}</code> (${l.domain_available_br ? "LIVRE para registro!" : "Já registrado"})</li>
            <li><strong>CMS Detectado (WhatCMS):</strong> ${l.detected_cms}</li>
            <li><strong>Tecnologias (BuiltWith / Wappalyzer):</strong> ${(l.tech_stack || []).join(", ") || "Nenhuma detectada"}</li>
            <li><strong>Possui Sistema Complexo (Agenda/Portal):</strong> ${l.has_complex_system ? "Sim" : "Não (Oportunidade de Expansão!)"}</li>
            <li><strong>Último Snapshot (Web Archive):</strong> ${l.wayback_last_seen || "Sem histórico recente"}</li>
          </ul>
        </div>

        <div style="font-weight:700; font-size:0.86rem; margin-bottom:8px;">Abrir Ferramentas Externas em 1 Clique:</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
          <a href="${ext.google_maps || "#"}" target="_blank" class="btn-secondary" style="text-decoration:none; text-align:center;">1. Google Maps ↗</a>
          <a href="${ext.casadosdados || "#"}" target="_blank" class="btn-secondary" style="text-decoration:none; text-align:center;">2. Casa dos Dados ↗</a>
          <a href="${ext.registro_br || "#"}" target="_blank" class="btn-secondary" style="text-decoration:none; text-align:center;">3. Registro.br ↗</a>
          <a href="${ext.downforeveryone || "#"}" target="_blank" class="btn-secondary" style="text-decoration:none; text-align:center;">4. DownForEveryone ↗</a>
          <a href="${ext.builtwith || "#"}" target="_blank" class="btn-secondary" style="text-decoration:none; text-align:center;">5. BuiltWith ↗</a>
          <a href="${ext.wappalyzer || "#"}" target="_blank" class="btn-secondary" style="text-decoration:none; text-align:center;">6. Wappalyzer ↗</a>
          <a href="${ext.whatcms || "#"}" target="_blank" class="btn-secondary" style="text-decoration:none; text-align:center;">7. WhatCMS ↗</a>
          <a href="${ext.web_archive || "#"}" target="_blank" class="btn-secondary" style="text-decoration:none; text-align:center;">8. Web Archive ↗</a>
        </div>
      </div>

      <!-- Coluna Direita: Central de Contato & Scripts Prontos -->
      <div>
        <div class="section-bar">Central de Contato &amp; Scripts Personalizados</div>

        <div class="tool-card" style="margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <strong style="font-size:0.88rem;">Script WhatsApp (Personalizado pela Dor)</strong>
            <div style="display:flex; gap:6px;">
              <button class="btn-secondary" style="padding:4px 10px; font-size:0.75rem;" onclick="copyText('modal-wpp-text')">Copiar Texto</button>
              ${
                sc.whatsapp_url
                  ? `<a href="${sc.whatsapp_url}" target="_blank" class="btn-whatsapp" onclick="markLeadContacted(${l.id})">Abrir WhatsApp ↗</a>`
                  : ""
              }
            </div>
          </div>
          <textarea id="modal-wpp-text" rows="6" style="width:100%; padding:8px; border:1px solid var(--border-warm); border-radius:6px; font-size:0.83rem; font-family:inherit;">${sc.whatsapp || ""}</textarea>
        </div>

        <div class="tool-card" style="margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <strong style="font-size:0.88rem;">Script Instagram DM</strong>
            <div style="display:flex; gap:6px;">
              <button class="btn-secondary" style="padding:4px 10px; font-size:0.75rem;" onclick="copyText('modal-ig-text')">Copiar DM</button>
              ${
                l.instagram
                  ? `<a href="${l.instagram}" target="_blank" class="btn-secondary" style="padding:4px 10px; font-size:0.75rem; text-decoration:none;">Abrir Instagram ↗</a>`
                  : ""
              }
            </div>
          </div>
          <textarea id="modal-ig-text" rows="3" style="width:100%; padding:8px; border:1px solid var(--border-warm); border-radius:6px; font-size:0.83rem; font-family:inherit;">${sc.instagram_dm || ""}</textarea>
        </div>

        <div class="tool-card" style="margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <strong style="font-size:0.88rem;">E-mail Consultivo (${sc.email_subject || ""})</strong>
            <div style="display:flex; gap:6px;">
              <button class="btn-secondary" style="padding:4px 10px; font-size:0.75rem;" onclick="copyText('modal-email-text')">Copiar E-mail</button>
              ${
                sc.mailto_url
                  ? `<a href="${sc.mailto_url}" class="btn-secondary" style="padding:4px 10px; font-size:0.75rem; text-decoration:none;">Abrir E-mail ↗</a>`
                  : ""
              }
            </div>
          </div>
          <textarea id="modal-email-text" rows="4" style="width:100%; padding:8px; border:1px solid var(--border-warm); border-radius:6px; font-size:0.83rem; font-family:inherit;">${sc.email_body || ""}</textarea>
        </div>

        <div style="display:flex; gap:8px; justify-content:flex-end;">
          <button class="btn-primary" onclick="enqueueSingleLead(${l.id}, 'whatsapp')">
            + Enfileirar para Robô Futuro (Outreach Queue)
          </button>
        </div>
      </div>
    </div>
  `;

  document.getElementById("lead-modal").classList.add("open");
}

function closeLeadModal() {
  document.getElementById("lead-modal").classList.remove("open");
}

function copyText(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.select();
  navigator.clipboard.writeText(el.value);
}

async function enqueueSingleLead(leadId, channel) {
  await fetch("/api/outreach/enqueue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lead_ids: [leadId], channels: [channel] }),
  });
  await loadHealthAndStats();
  alert("Lead adicionado à fila de automação futura (/api/outreach/queue)!");
}

async function enqueueSelectedLeads(channel) {
  const ids = Array.from(document.querySelectorAll(".lead-checkbox:checked")).map((cb) =>
    parseInt(cb.value, 10)
  );
  if (!ids.length) {
    alert("Marque pelo menos um lead na tabela para enviar à fila de automação.");
    return;
  }
  const res = await fetch("/api/outreach/enqueue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lead_ids: ids, channels: [channel] }),
  });
  const data = await res.json();
  await loadHealthAndStats();
  alert(`${data.enqueued_count} disparo(s) preparados na fila de automação futura!`);
}

async function openQueueModal() {
  const res = await fetch("/api/outreach/queue");
  const items = await res.json();
  const body = document.getElementById("queue-modal-body");

  if (!items.length) {
    body.innerHTML = `<p style="color:var(--text-muted);">A fila está vazia. Selecione leads na tabela e clique em "Enviar Selecionados p/ Fila Bot Futuro".</p>`;
  } else {
    body.innerHTML = `
      <table class="table-leads">
        <thead>
          <tr>
            <th>ID</th>
            <th>Empresa</th>
            <th>Canal / Destino</th>
            <th>Status</th>
            <th>Mensagem Preparada</th>
          </tr>
        </thead>
        <tbody>
          ${items
            .map(
              (it) => `
            <tr>
              <td>#${it.id}</td>
              <td><strong>${it.lead_title || "Lead #" + it.lead_id}</strong><br/><small>${it.lead_city || ""}</small></td>
              <td><code>${it.channel}</code><br/>${it.recipient}</td>
              <td><span class="pain-tag">${it.status}</span></td>
              <td style="font-size:0.8rem; max-width:420px; white-space:pre-wrap;">${it.message_body}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;
  }
  document.getElementById("queue-modal").classList.add("open");
}

function closeQueueModal() {
  document.getElementById("queue-modal").classList.remove("open");
}

function openManualLeadModal() {
  document.getElementById("manual-modal-title").textContent = "Cadastrar Novo Lead Manualmente + Rodar Raio-X";
  document.getElementById("manual-modal-body").innerHTML = `
    <div style="display:flex; flex-direction:column; gap:10px;">
      <input id="m-title" placeholder="Nome da Empresa (ex: Clínica Sorriso)" style="padding:9px; border:1px solid var(--border-warm); border-radius:7px;" />
      <input id="m-city" value="Campinas" placeholder="Cidade" style="padding:9px; border:1px solid var(--border-warm); border-radius:7px;" />
      <input id="m-phone" placeholder="Telefone / WhatsApp (ex: 19 99876-5432)" style="padding:9px; border:1px solid var(--border-warm); border-radius:7px;" />
      <input id="m-website" placeholder="Website atual (deixe em branco se não tiver)" style="padding:9px; border:1px solid var(--border-warm); border-radius:7px;" />
      <input id="m-email" placeholder="E-mail (opcional)" style="padding:9px; border:1px solid var(--border-warm); border-radius:7px;" />
      <button class="btn-primary" onclick="submitManualLead()">Salvar &amp; Executar Raio-X</button>
    </div>
  `;
  document.getElementById("manual-modal").classList.add("open");
}

function openCsvImportModal() {
  document.getElementById("manual-modal-title").textContent = "Importar CSV (Gerado pelo scrape.py ou Casa dos Dados)";
  document.getElementById("manual-modal-body").innerHTML = `
    <div style="display:flex; flex-direction:column; gap:10px;">
      <p style="margin:0; font-size:0.84rem; color:var(--text-muted);">
        Cole abaixo o conteúdo do arquivo CSV (com cabeçalho <code>title,phone,emails,website,category,address,review_rating,review_count</code>):
      </p>
      <textarea id="csv-paste-area" rows="8" placeholder="title,phone,emails,website,category,address,review_rating,review_count&#10;Empresa Exemplo,(19) 99999-0000,contato@exemplo.com,,Dentista,Rua A 10,4.9,45" style="width:100%; padding:8px; border:1px solid var(--border-warm); border-radius:7px; font-family:monospace; font-size:0.8rem;"></textarea>
      <button class="btn-primary" onclick="submitCsvImport()">Importar &amp; Qualificar Leads</button>
    </div>
  `;
  document.getElementById("manual-modal").classList.add("open");
}

function closeManualModal() {
  document.getElementById("manual-modal").classList.remove("open");
}

async function submitManualLead() {
  const title = document.getElementById("m-title").value.trim();
  if (!title) return;
  await fetch("/api/leads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      city: document.getElementById("m-city").value.trim() || "Campinas",
      phone: document.getElementById("m-phone").value.trim(),
      website: document.getElementById("m-website").value.trim(),
      emails: document.getElementById("m-email").value.trim(),
      run_xray: true,
    }),
  });
  closeManualModal();
  await Promise.all([loadHealthAndStats(), loadLeads()]);
}

async function submitCsvImport() {
  const csvText = document.getElementById("csv-paste-area").value.trim();
  if (!csvText) return;
  const city = document.getElementById("input-city").value.trim() || "Campinas";
  await fetch("/api/leads/import-csv", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ csv_text: csvText, city, state: "SP", run_xray: true }),
  });
  closeManualModal();
  await Promise.all([loadHealthAndStats(), loadLeads()]);
}

window.addEventListener("DOMContentLoaded", initDashboard);
