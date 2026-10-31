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
  await Promise.all([
    loadHealthAndStats(),
    loadNiches(),
    loadLeads(),
    runEmbeddedMapsEngineCheck(),
  ]);
  if (CURRENT_LEADS.length > 0) {
    populateEmbeddedToolsFromLead(CURRENT_LEADS[0]);
  }
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
    fb.innerHTML = `<strong style="color:var(--emerald);">✓ Busca concluída!</strong> ${data.total_leads_processed} leads qualificados com Raio-X das 8 ferramentas embutidas e scripts prontos.`;
    await Promise.all([loadHealthAndStats(), loadLeads(), runEmbeddedMapsEngineCheck()]);
    if (CURRENT_LEADS.length > 0) {
      populateEmbeddedToolsFromLead(CURRENT_LEADS[0]);
    }
  } catch (err) {
    fb.innerHTML = `<strong style="color:var(--crimson);">✗ Erro:</strong> ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Buscar & Rodar Raio-X";
  }
}

// ============================================================================
// AS 8 FERRAMENTAS 100% EMBUTIDAS NO PAINEL (ZERO LINKS EXTERNOS)
// ============================================================================

async function runEmbeddedMapsEngineCheck() {
  const city = (document.getElementById("input-city")?.value || "Campinas").trim();
  const state = (document.getElementById("input-state")?.value || "SP").trim();
  const box = document.getElementById("embedded-maps-box");
  if (!box) return;
  try {
    const res = await fetch(
      `/api/tools/maps-engine?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}&grid_size=2`
    );
    const data = await res.json();
    const eng = data.engine || {};
    const geo = data.geocoding || {};
    const pillClass = eng.online ? "ok" : "warn";
    const statusLabel = eng.online
      ? `● Container Ativo (${eng.base_url} • ${eng.count || 0} jobs no motor)`
      : `○ Container Offline (${eng.base_url})`;

    box.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:6px;">
        <span class="embedded-pill ${pillClass}">${statusLabel}</span>
        <span class="embedded-pill">Coordenadas ${geo.city}-${geo.state}: <strong>${geo.lat}, ${geo.lon}</strong></span>
        <span class="embedded-pill">Malha Grid: <strong>${geo.cells_count} quadrantes</strong></span>
      </div>
      <div style="font-size:0.76rem; color:var(--text-muted);">
        Imagem: <code>gosom/google-maps-scraper:v1.18.1</code> • Fonte Geo: <code>${geo.source}</code>
      </div>
    `;
  } catch (err) {
    box.innerHTML = `<span class="embedded-pill err">Erro ao inspecionar motor Maps: ${err.message}</span>`;
  }
}

async function startDockerEngineEmbedded() {
  const box = document.getElementById("embedded-maps-box");
  if (box) {
    box.innerHTML = `Iniciando container Docker <code>gmaps-scraper</code> via <code>docker compose up -d</code>...`;
  }
  try {
    await fetch("/api/engine/start", { method: "POST" });
    await Promise.all([loadHealthAndStats(), runEmbeddedMapsEngineCheck()]);
  } catch (err) {
    if (box) box.innerHTML = `<span class="embedded-pill err">Falha ao iniciar Docker: ${err.message}</span>`;
  }
}

async function runEmbeddedCnpjLookup(importLead = false) {
  const input = document.getElementById("embedded-cnpj-input")?.value.trim() || "";
  const box = document.getElementById("casadosdados-box");
  if (!input) {
    alert("Digite um CNPJ (14 números) no campo do módulo Casa dos Dados / CNPJ.");
    return;
  }
  const firstNiche = Array.from(SELECTED_NICHES)[0] || "geral";
  box.innerHTML = "Consultando dados societários e cadastrais do CNPJ...";
  try {
    const res = await fetch(
      `/api/tools/cnpj?cnpj=${encodeURIComponent(input)}&import_as_lead=${importLead ? "true" : "false"}&niche_slug=${encodeURIComponent(firstNiche)}`
    );
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "CNPJ inválido");
    }
    const c = data.cnpj_data;
    const sociosHtml = (c.qsa || [])
      .map((s) => `${s.nome_socio} (${s.qualificacao_socio})`)
      .join(" • ");

    box.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px; flex-wrap:wrap;">
        <div>
          <strong>${c.nome_fantasia || c.razao_social}</strong>
          <span class="embedded-pill ok">${c.situacao_cadastral}</span>
          <span class="embedded-pill">Abertura: ${c.data_inicio_atividade || "N/D"}</span>
        </div>
        <button class="btn-secondary" style="padding:3px 9px; font-size:0.74rem;" onclick="runEmbeddedCnpjLookup(true)">
          + Converter este CNPJ em Lead
        </button>
      </div>
      <div style="margin-top:4px; font-size:0.78rem; color:var(--text-muted);">
        <strong>Razão Social:</strong> ${c.razao_social} • <strong>CNPJ:</strong> ${c.cnpj_formatted}<br/>
        <strong>CNAE Principal:</strong> ${c.cnae_fiscal} — ${c.cnae_fiscal_descricao}<br/>
        <strong>Quadro Societário (QSA):</strong> ${sociosHtml || "Não informado"} • <strong>Capital:</strong> R$ ${(c.capital_social || 0).toLocaleString("pt-BR")}<br/>
        <strong>Contato Receita:</strong> 📞 ${c.telefone || "Sem telefone"} • ✉️ ${c.email || "Sem e-mail"} • 📍 ${c.municipio}-${c.uf}<br/>
        <strong>Domínio Sugerido:</strong> <code>${c.suggested_domain}</code>
      </div>
      ${
        data.imported_lead
          ? `<div style="margin-top:6px; color:var(--emerald); font-weight:700;">✓ Empresa convertida e salva na tabela de Leads (#${data.imported_lead.id})!</div>`
          : ""
      }
    `;
    if (data.imported_lead) {
      await Promise.all([loadHealthAndStats(), loadLeads()]);
    }
  } catch (err) {
    box.innerHTML = `<span class="embedded-pill err">✗ ${err.message}</span>`;
  }
}

async function runEmbeddedCnaeDiscovery(importAsLeads = true) {
  const city = (document.getElementById("input-city")?.value || "Campinas").trim();
  const state = (document.getElementById("input-state")?.value || "SP").trim();
  const slugs = Array.from(SELECTED_NICHES);
  const box = document.getElementById("casadosdados-box");
  box.innerHTML = `Varrendo empresas recém-abertas por CNAE em ${city}-${state}...`;

  try {
    const res = await fetch("/api/tools/cnpj-discover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        city,
        state,
        niche_slugs: slugs.length ? slugs : ["clinicas-odontologicas", "escritorios-advocacia"],
        days_opened: 90,
        import_as_leads: importAsLeads,
      }),
    });
    const data = await res.json();
    const disc = data.discovery || {};
    const companies = disc.companies || [];

    box.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; flex-wrap:wrap; gap:6px;">
        <span class="embedded-pill ok">✓ ${companies.length} Empresas Recém-Abertas Encontradas (${city}-${state})</span>
        ${
          data.imported_count > 0
            ? `<span class="embedded-pill ok">+${data.imported_count} importadas p/ Tabela de Leads!</span>`
            : ""
        }
      </div>
      <div style="max-height:155px; overflow-y:auto; display:flex; flex-direction:column; gap:6px;">
        ${companies
          .map(
            (c) => `
          <div style="padding:6px 8px; background:#ffffff; border:1px solid var(--border-warm); border-radius:6px; font-size:0.77rem;">
            <div style="display:flex; justify-content:space-between; gap:6px;">
              <strong>${c.nome_fantasia}</strong>
              <span style="color:var(--brand-blue); font-weight:700;">Abertura: ${c.opened_date}</span>
            </div>
            <div style="color:var(--text-muted);">
              CNPJ: <code>${c.cnpj}</code> • CNAE: <code>${c.cnae_fiscal}</code> • Sócio: ${c.socio_administrador}<br/>
              📞 ${c.phone} • ✉️ ${c.email} • Domínio Livre: <code>${c.suggested_domain}</code>
            </div>
          </div>
        `
          )
          .join("")}
      </div>
    `;
    if (importAsLeads) {
      await Promise.all([loadHealthAndStats(), loadLeads()]);
    }
  } catch (err) {
    box.innerHTML = `<span class="embedded-pill err">Erro ao descobrir empresas por CNAE: ${err.message}</span>`;
  }
}

function renderRegistroBrBox(data) {
  const out = document.getElementById("quick-domain-result");
  if (!out || !data) return;
  const variationsHtml = (data.variations || [])
    .map(
      (v) =>
        `<span class="embedded-pill ${v.available ? "ok" : "warn"}">${v.available ? "✓ LIVRE" : "● Ocupado"}: ${v.domain}</span>`
    )
    .join("");

  if (data.available) {
    out.innerHTML = `
      <div style="margin-bottom:4px;">
        <span class="embedded-pill ok">✓ DOMÍNIO LIVRE NO REGISTRO.BR: <strong>${data.domain}</strong></span>
        <span class="embedded-pill">Status: Disponível para Registro Imediato</span>
      </div>
      <div style="font-size:0.76rem; color:var(--text-muted); margin-bottom:4px;">
        Argumento de venda pronto: você pode registrar <code>${data.domain}</code> hoje para o cliente!
      </div>
      <div><strong>3 Variações Testadas:</strong> ${variationsHtml}</div>
    `;
  } else {
    out.innerHTML = `
      <div style="margin-bottom:4px;">
        <span class="embedded-pill warn">● DOMÍNIO JÁ REGISTRADO: <strong>${data.domain}</strong></span>
        ${data.owner_name ? `<span class="embedded-pill">Titular: ${data.owner_name}</span>` : ""}
        ${data.owner_handle ? `<span class="embedded-pill">Doc/ID: ${data.owner_handle}</span>` : ""}
      </div>
      <div style="font-size:0.76rem; color:var(--text-muted); margin-bottom:4px;">
        ${data.created_at ? `Criado em: <strong>${data.created_at}</strong> • ` : ""}
        ${data.expires_at ? `Expira em: <strong>${data.expires_at}</strong> • ` : ""}
        DNS: <code>${(data.nameservers || []).join(", ") || "Padrão"}</code>
      </div>
      <div><strong>Alternativas .com.br Livres:</strong> ${variationsHtml}</div>
    `;
  }
}

async function checkQuickDomain(customQuery) {
  const inputEl = document.getElementById("quick-domain-input");
  const query = (customQuery || inputEl?.value || "").trim();
  const city = (document.getElementById("input-city")?.value || "Campinas").trim();
  const out = document.getElementById("quick-domain-result");
  if (!query) return;
  if (inputEl && customQuery) inputEl.value = customQuery;
  out.innerHTML = "Consultando servidor RDAP Oficial do Registro.br...";
  try {
    const res = await fetch(
      `/api/tools/registro-br?query=${encodeURIComponent(query)}&city=${encodeURIComponent(city)}`
    );
    const data = await res.json();
    renderRegistroBrBox(data);
  } catch (e) {
    out.innerHTML = `<span class="embedded-pill err">Erro ao consultar RDAP: ${e.message}</span>`;
  }
}

function renderSiteHealthBox(data, targetUrl) {
  const box = document.getElementById("quick-health-result");
  if (!box || !data) return;
  const pillClass = data.site_in_air ? (data.has_ssl ? "ok" : "warn") : "err";
  const statusTitle = !data.has_website
    ? "SEM SITE CADASTRADO"
    : data.site_in_air
    ? `ONLINE (HTTP ${data.http_status} • ${data.response_time_ms}ms)`
    : `FORA DO AR / INACESSÍVEL (${data.verdict || "ERRO"})`;

  box.innerHTML = `
    <div style="display:flex; flex-wrap:wrap; gap:4px; margin-bottom:4px;">
      <span class="embedded-pill ${pillClass}">${statusTitle}</span>
      <span class="embedded-pill">IP / DNS: <strong>${data.resolved_ip || (data.dns_ok ? "Resolvido" : "Falha DNS / Sem Host")}</strong></span>
      <span class="embedded-pill ${data.has_ssl ? "ok" : "warn"}">${data.has_ssl ? "🔒 HTTPS Válido" : "⚠️ Sem SSL / HTTP Inseguro"}</span>
    </div>
    <div style="font-size:0.76rem; color:var(--text-muted);">
      <strong>Alvo:</strong> <code>${targetUrl || data.final_url || "Nenhum"}</code> •
      <strong>Emissor SSL:</strong> ${data.ssl_issuer || "N/A"} •
      <strong>Veredito:</strong> <code>${data.verdict || "ANALISADO"}</code>
    </div>
  `;
}

async function runEmbeddedSiteHealth(customUrl) {
  const inputEl = document.getElementById("quick-health-input");
  const url = (customUrl || inputEl?.value || "").trim();
  const box = document.getElementById("quick-health-result");
  if (!url) return;
  if (inputEl && customUrl) inputEl.value = customUrl;
  box.innerHTML = `Testando resolução DNS, certificado SSL e latência HTTP de <code>${url}</code>...`;
  try {
    const res = await fetch(`/api/tools/site-health?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    renderSiteHealthBox(data, url);
  } catch (err) {
    box.innerHTML = `<span class="embedded-pill err">Erro ao testar site: ${err.message}</span>`;
  }
}

function renderAll4RightColumnScanners(reports, leadOrXray, targetLabel) {
  const bw = reports.builtwith || {};
  const wp = reports.wappalyzer || {};
  const wc = reports.whatcms || {};
  const wb = reports.wayback || {};

  ["builtwith", "wappalyzer", "whatcms", "wayback"].forEach((id) => {
    const lbl = document.getElementById(`${id}-target-label`);
    if (lbl) lbl.textContent = targetLabel || "Analisado";
  });

  // 5. BuiltWith Box
  const bwBox = document.getElementById("embedded-builtwith-box");
  if (bwBox) {
    const pixels = (bw.analytics_pixels || []).length
      ? bw.analytics_pixels.map((p) => `<span class="embedded-pill ok">${p}</span>`).join("")
      : `<span class="embedded-pill warn">Sem Pixel GA4 / Meta Ads</span>`;
    const chats = (bw.chat_widgets || []).length
      ? bw.chat_widgets.map((c) => `<span class="embedded-pill ok">${c}</span>`).join("")
      : `<span class="embedded-pill warn">Sem Widget de WhatsApp/Chat</span>`;

    bwBox.innerHTML = `
      <div style="margin-bottom:4px;">
        <span class="embedded-pill">Servidor: <strong>${bw.server || "Não detectado"}</strong></span>
        <span class="embedded-pill">CDN: <strong>${bw.cdn || "Nenhuma"}</strong></span>
        <span class="embedded-pill">Infra: <strong>${bw.hosting_hints || "Padrão"}</strong></span>
      </div>
      <div style="margin-bottom:3px;"><strong>Pixels &amp; Analytics:</strong> ${pixels}</div>
      <div><strong>Widgets de Conversão:</strong> ${chats}</div>
    `;
  }

  // 6. Wappalyzer Box
  const wpBox = document.getElementById("embedded-wappalyzer-box");
  if (wpBox) {
    const jsList = (wp.js_frameworks || ["Sem JS SPA"]).map((j) => `<span class="embedded-pill">${j}</span>`).join("");
    const cssList = (wp.css_ui || ["CSS Padrão"]).map((c) => `<span class="embedded-pill">${c}</span>`).join("");
    const seo = wp.seo_meta || {};
    wpBox.innerHTML = `
      <div style="margin-bottom:4px;"><strong>Frameworks JS:</strong> ${jsList}</div>
      <div style="margin-bottom:4px;"><strong>UI &amp; Estilo:</strong> ${cssList}</div>
      <div>
        <span class="embedded-pill ${seo.is_mobile_viewport ? "ok" : "err"}">${seo.is_mobile_viewport ? "✓ Mobile Viewport OK" : "✗ Sem Mobile Viewport"}</span>
        <span class="embedded-pill ${seo.has_title ? "ok" : "warn"}">${seo.has_title ? "✓ Tag Title" : "✗ Sem Title"}</span>
        <span class="embedded-pill ${seo.has_meta_description ? "ok" : "warn"}">${seo.has_meta_description ? "✓ Meta Description" : "✗ Sem Meta Description"}</span>
        <span class="embedded-pill ${seo.has_opengraph ? "ok" : "warn"}">${seo.has_opengraph ? "✓ OpenGraph" : "○ Sem OpenGraph"}</span>
      </div>
    `;
  }

  // 7. WhatCMS Box
  const wcBox = document.getElementById("embedded-whatcms-box");
  if (wcBox) {
    const opps = (wc.missing_systems_opportunities || [])
      .map((o) => `<li><strong>Oportunidade:</strong> ${o}</li>`)
      .join("");
    const plugins = (wc.detected_plugins || []).length
      ? wc.detected_plugins.join(", ")
      : "Nenhum plugin exposto";
    wcBox.innerHTML = `
      <div style="margin-bottom:4px;">
        <span class="embedded-pill ${wc.cms_name === "Sem Site" || wc.cms_name === "Wix" ? "warn" : "ok"}">CMS: <strong>${wc.cms_name || leadOrXray.detected_cms || "Desconhecido"}</strong> (${wc.cms_version || "Padrão"})</span>
        <span class="embedded-pill">E-commerce: <strong>${wc.ecommerce_engine || "Nenhum"}</strong></span>
        <span class="embedded-pill ${wc.has_complex_system ? "ok" : "warn"}">${wc.has_complex_system ? "Possui Sistema Integrado" : "Sem Sistema de Agendamento/Portal"}</span>
      </div>
      <div style="font-size:0.76rem; color:var(--text-muted); margin-bottom:4px;">
        <strong>Plugins detectados:</strong> ${plugins}
      </div>
      ${
        opps
          ? `<ul style="margin:4px 0 0; padding-left:18px; font-size:0.76rem; color:var(--brand-blue);">${opps}</ul>`
          : ""
      }
    `;
  }

  // 8. Web Archive Box
  const wbBox = document.getElementById("embedded-wayback-box");
  if (wbBox) {
    const firstSeen = wb.wayback_first_seen || leadOrXray.wayback_first_seen || "Sem registro";
    const lastSeen = wb.wayback_last_seen || leadOrXray.wayback_last_seen || "Sem registro";
    const days = wb.wayback_days_since_update ?? leadOrXray.wayback_days_since_update;
    const tl = (wb.snapshots_timeline || [])
      .slice(-5)
      .map((s) => `<span class="embedded-pill">${s.date} (HTTP ${s.status})</span>`)
      .join("");

    wbBox.innerHTML = `
      <div style="margin-bottom:4px;">
        <span class="embedded-pill ${days && days > 365 ? "warn" : "ok"}">
          ${days !== null && days !== undefined ? `⏱️ ${days} dias desde a última captura` : "Sem capturas no Archive.org"}
        </span>
        <span class="embedded-pill">1ª Captura: <strong>${firstSeen}</strong></span>
        <span class="embedded-pill">Última: <strong>${lastSeen}</strong></span>
      </div>
      <div style="font-size:0.76rem; color:var(--text-muted);">
        <strong>Veredito Histórico:</strong> <code>${wb.abandonment_verdict || "ANALISADO"}</code>
      </div>
      ${tl ? `<div style="margin-top:4px;"><strong>Linha do Tempo CDX:</strong> ${tl}</div>` : ""}
    `;
  }
}

async function runEmbeddedFullXrayInput() {
  const url = (document.getElementById("quick-xray-url")?.value || "").trim();
  const city = (document.getElementById("input-city")?.value || "Campinas").trim();
  if (!url) {
    alert("Digite uma URL ou domínio no campo 'URL p/ Raio-X' (ex: http://mastergroup-wix-demo.com.br).");
    return;
  }
  const bwBox = document.getElementById("embedded-builtwith-box");
  if (bwBox) bwBox.innerHTML = `Executando Raio-X profundo em <code>${url}</code>...`;

  try {
    const res = await fetch(
      `/api/tools/site-xray?url=${encodeURIComponent(url)}&company_name=${encodeURIComponent(url)}&city=${encodeURIComponent(city)}`
    );
    const xray = await res.json();
    const reports = (xray.external_tools_links || {}).embedded_reports || {};
    renderRegistroBrBox(reports.registro_br);
    renderSiteHealthBox(
      {
        has_website: xray.has_website,
        site_in_air: xray.site_in_air,
        http_status: xray.http_status,
        has_ssl: xray.has_ssl,
        response_time_ms: xray.response_time_ms,
        ...(reports.dns_ssl || {}),
      },
      url
    );
    renderAll4RightColumnScanners(reports, xray, url);
  } catch (err) {
    if (bwBox) bwBox.innerHTML = `<span class="embedded-pill err">Erro no Raio-X: ${err.message}</span>`;
  }
}

function populateEmbeddedToolsFromLead(lead) {
  if (!lead) return;
  const reports = ((lead.external_tools_links || {}).embedded_reports) || {};
  const domInput = document.getElementById("quick-domain-input");
  if (domInput) domInput.value = lead.suggested_domain || lead.title || "";
  const healthInput = document.getElementById("quick-health-input");
  if (healthInput) healthInput.value = lead.website || lead.suggested_domain || "";
  const xrayInput = document.getElementById("quick-xray-url");
  if (xrayInput) xrayInput.value = lead.website || lead.suggested_domain || "";
  if (lead.cnpj) {
    const cnpjInput = document.getElementById("embedded-cnpj-input");
    if (cnpjInput) cnpjInput.value = lead.cnpj;
  }

  if (reports.registro_br) {
    renderRegistroBrBox(reports.registro_br);
  }
  renderSiteHealthBox(
    {
      has_website: lead.has_website,
      site_in_air: lead.site_in_air,
      http_status: lead.http_status,
      has_ssl: lead.has_ssl,
      response_time_ms: lead.response_time_ms,
      ...(reports.dns_ssl || {}),
    },
    lead.website || "Sem site cadastrado"
  );
  renderAll4RightColumnScanners(reports, lead, `${lead.title} (${lead.website || "Sem site"})`);
}

function inspectLeadInEmbeddedTools(leadId) {
  const lead = CURRENT_LEADS.find((item) => item.id === leadId);
  if (!lead) return;
  populateEmbeddedToolsFromLead(lead);
  window.scrollTo({ top: 320, behavior: "smooth" });
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
          <div style="margin-top:4px; display:flex; gap:6px; flex-wrap:wrap;">
            <button class="btn-secondary" style="padding:3px 8px; font-size:0.72rem;" onclick="checkQuickDomain('${l.suggested_domain}')">
              Escanear RDAP no Painel
            </button>
          </div>
        </td>
        <td>
          <div style="display:flex; flex-wrap:wrap; gap:6px;">
            ${
              sc.whatsapp_url
                ? `<a href="${sc.whatsapp_url}" target="_blank" class="btn-whatsapp" onclick="markLeadContacted(${l.id})">WhatsApp 1-Clique ↗</a>`
                : ""
            }
            <button class="btn-secondary" style="padding:6px 10px; font-size:0.76rem;" onclick="inspectLeadInEmbeddedTools(${l.id})">
              Inspecionar nas 8 Ferramentas
            </button>
            <button class="btn-secondary" style="padding:6px 10px; font-size:0.76rem;" onclick="openLeadModal(${l.id})">
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

async function reanalyzeLeadEmbedded(leadId) {
  const btn = document.getElementById("btn-reanalyze-modal");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Reexecutando 8 Scanners...";
  }
  await fetch(`/api/leads/${leadId}/reanalyze`, { method: "POST" });
  await loadLeads();
  await openLeadModal(leadId);
}

async function openLeadModal(leadId) {
  const res = await fetch(`/api/leads/${leadId}`);
  const l = await res.json();
  const sc = l.outreach_scripts || {};
  const ext = l.external_tools_links || {};
  const rep = ext.embedded_reports || {};
  const bw = rep.builtwith || {};
  const wp = rep.wappalyzer || {};
  const wc = rep.whatcms || {};
  const reg = rep.registro_br || {};
  const dns = rep.dns_ssl || {};

  populateEmbeddedToolsFromLead(l);

  document.getElementById("modal-lead-title").textContent = `${l.title} — Score ${l.opportunity_score}/100`;
  document.getElementById("modal-lead-subtitle").textContent = `${l.address || l.city} • 📞 ${l.phone || "Sem telefone"} • ✉️ ${l.emails || "Sem e-mail"}`;

  const missingOpps = (wc.missing_systems_opportunities || [])
    .map((o) => `<li>${o}</li>`)
    .join("");
  const variationsPills = (reg.variations || [])
    .map((v) => `<span class="embedded-pill ${v.available ? "ok" : "warn"}">${v.available ? "✓ LIVRE" : "● Ocupado"}: ${v.domain}</span>`)
    .join("");

  document.getElementById("modal-lead-body").innerHTML = `
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(430px, 1fr)); gap:20px;">
      <!-- Coluna Esquerda: Diagnóstico Embutido das 8 Ferramentas (Zero Links Externos) -->
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <div class="section-bar" style="margin-bottom:0;">Diagnóstico Embutido (8 Ferramentas)</div>
          <button id="btn-reanalyze-modal" class="btn-secondary" style="padding:5px 10px; font-size:0.76rem;" onclick="reanalyzeLeadEmbedded(${l.id})">
            ↻ Reexecutar Scanners Agora
          </button>
        </div>

        <div class="tool-card" style="margin-bottom:10px;">
          <div style="font-weight:700; margin-bottom:4px;">Resumo Comercial (${SERVICE_LABELS[l.recommended_service] || l.recommended_service})</div>
          <div style="font-size:0.86rem; color:var(--text-ink);">${l.pain_summary}</div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
          <div class="embedded-box" style="margin-top:0;">
            <strong>1. google.com/maps</strong><br/>
            ⭐ ${l.review_rating} (${l.review_count} avaliações)<br/>
            Categoria: ${l.category || l.niche_slug}<br/>
            Cidade: ${l.city}-${l.state}
          </div>
          <div class="embedded-box" style="margin-top:0;">
            <strong>2. casadosdados / CNPJ</strong><br/>
            CNPJ: <code>${l.cnpj || "Não informado"}</code><br/>
            Abertura: ${l.opened_date || "Não informada"}<br/>
            Origem: <code>${l.source}</code>
          </div>
          <div class="embedded-box" style="margin-top:0;">
            <strong>3. registro.br (RDAP)</strong><br/>
            Domínio: <code>${l.suggested_domain}</code><br/>
            Status: <strong style="color:${l.domain_available_br ? "var(--emerald)" : "var(--amber)"};">${l.domain_available_br ? "LIVRE P/ REGISTRO" : "Já Registrado"}</strong><br/>
            ${variationsPills}
          </div>
          <div class="embedded-box" style="margin-top:0;">
            <strong>4. downforeveryone (DNS/SSL)</strong><br/>
            Status: <strong>${l.has_website ? (l.site_in_air ? "ONLINE (HTTP " + l.http_status + ")" : "FORA DO AR") : "Sem Site"}</strong><br/>
            IP: <code>${dns.resolved_ip || "N/A"}</code> • ${l.response_time_ms || 0}ms<br/>
            SSL: ${l.has_ssl ? "🔒 HTTPS Ativo" : "⚠️ Sem SSL"}
          </div>
          <div class="embedded-box" style="margin-top:0;">
            <strong>5. builtwith.com</strong><br/>
            Servidor: ${bw.server || "N/A"}<br/>
            Pixels: ${(bw.analytics_pixels || []).join(", ") || "Nenhum pixel"}<br/>
            Chat: ${(bw.chat_widgets || []).join(", ") || "Sem widget"}
          </div>
          <div class="embedded-box" style="margin-top:0;">
            <strong>6. wappalyzer.com</strong><br/>
            JS: ${(wp.js_frameworks || []).join(", ") || "N/A"}<br/>
            CSS: ${(wp.css_ui || []).join(", ") || "N/A"}<br/>
            Mobile Viewport: ${l.is_mobile_friendly ? "✓ Responsivo" : "✗ Não responsivo"}
          </div>
          <div class="embedded-box" style="margin-top:0;">
            <strong>7. whatcms.org &amp; Sistemas</strong><br/>
            CMS: <strong>${l.detected_cms}</strong><br/>
            Sistema Complexo: ${l.has_complex_system ? "Sim" : "Não possui"}
            ${missingOpps ? `<ul style="margin:4px 0 0; padding-left:15px; font-size:0.73rem; color:var(--brand-blue);">${missingOpps}</ul>` : ""}
          </div>
          <div class="embedded-box" style="margin-top:0;">
            <strong>8. web.archive.org (CDX)</strong><br/>
            1ª Captura: ${l.wayback_first_seen || "Sem arquivo"}<br/>
            Última: ${l.wayback_last_seen || "Sem arquivo"}<br/>
            Inatividade: ${l.wayback_days_since_update != null ? l.wayback_days_since_update + " dias" : "N/A"}
          </div>
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
