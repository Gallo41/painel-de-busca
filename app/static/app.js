/* Painel de Busca — front-end (lista + central de contato).
   Dados vêm de /api/leads (reais, do motor Google Maps em Docker). Filtros rodam no navegador: instantâneos. */

let ALL_NICHES = [];
let SELECTED_NICHES = new Set(["clinicas-odontologicas", "escritorios-advocacia", "imobiliarias-corretores"]);
let ALL_LEADS = [];
let CURRENT_LEADS = [];
let SCOPE_CITY = "";
const PAGE = 50;
const state = { tab: "ALL", limit: PAGE, selectedId: null, kpiNoSite: false, kpiContacted: false };

const SERVICE_LABELS = {
  SITE_NOVO: "Site novo",
  REFORMA_SITE: "Reforma",
  SISTEMA_COMPLEXO: "Sistema",
};
const SERVICE_LONG = {
  SITE_NOVO: "Criação de site profissional",
  REFORMA_SITE: "Reforma de site",
  SISTEMA_COMPLEXO: "Sistema web sob medida",
};
const PILL_CLASS = { SITE_NOVO: "site", REFORMA_SITE: "reforma", SISTEMA_COMPLEXO: "sistema" };

const $ = (id) => document.getElementById(id);
const esc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtInt = (n) => Number(n || 0).toLocaleString("pt-BR");
const fmtRating = (n) => (Number(n) > 0 ? Number(n).toFixed(1).replace(".", ",") : "");

/* ---------- classificação e dados derivados ---------- */
function offerOf(l) {
  if (l.recommended_service === "SISTEMA_COMPLEXO" || l.primary_pain === "OPORTUNIDADE_SISTEMA") return "SISTEMA_COMPLEXO";
  if (l.primary_pain === "SITE_FORA_DO_AR" || l.primary_pain === "SITE_AMADOR_ANTIGO" || l.recommended_service === "REFORMA_SITE")
    return "REFORMA_SITE";
  return "SITE_NOVO";
}
const hasNoSite = (l) => !l.has_website || !!l.is_social_only_url;
const waNumber = (l) => (((l.outreach_scripts || {}).automation_payload || {}).whatsapp_number || l.whatsapp_clean || "").trim();
const isContacted = (l) => ["contatado", "respondeu", "reuniao", "fechado"].includes(l.lead_status);

function readyReportOf(l) {
  const rr = (l.outreach_scripts || {}).ready_report;
  if (rr && Array.isArray(rr.bullets)) return rr;
  const offer = offerOf(l);
  return {
    what_to_sell: SERVICE_LONG[offer],
    ticket_range: offer === "SISTEMA_COMPLEXO" ? "R$ 3.500 a R$ 8.000" : offer === "REFORMA_SITE" ? "R$ 1.800 a R$ 3.500" : "R$ 1.200 a R$ 2.500",
    executive_pitch: l.pain_summary || "",
    bullets: [],
  };
}

/* ---------- inicialização ---------- */
async function initDashboard() {
  bindShortcuts();
  renderSkeleton();
  await Promise.all([loadHealthAndStats(), loadNiches()]);
  await loadLeads();
  window.addEventListener("hashchange", routeFromHash);
  window.addEventListener("beforeprint", () => {
    state.limit = Infinity;
    renderRows();
  });
  window.addEventListener("afterprint", () => {
    state.limit = PAGE;
    renderRows();
  });
  routeFromHash();
}

function routeFromHash() {
  const view = location.hash === "#ferramentas" ? "ferramentas" : "clientes";
  $("view-clientes").hidden = view !== "clientes";
  $("view-ferramentas").hidden = view !== "ferramentas";
  document.querySelectorAll("[data-nav]").forEach((a) => {
    if (a.dataset.nav === view) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  $("sidebar").classList.remove("open");
  if (view === "ferramentas") {
    const lead = ALL_LEADS.find((x) => x.id === state.selectedId) || CURRENT_LEADS[0];
    runEmbeddedMapsEngineCheck();
    if (lead) populateEmbeddedToolsFromLead(lead);
  }
}

function toggleSidebar() {
  $("sidebar").classList.toggle("open");
}

function bindShortcuts() {
  document.addEventListener("keydown", (e) => {
    const tag = (e.target.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "textarea" || tag === "select";
    if (e.key === "/" && !typing) {
      e.preventDefault();
      $("filter-search").focus();
      return;
    }
    if (e.key === "Escape") {
      closeLeadModal();
      closeQueueModal();
      closeManualModal();
      closeDetailOverlay();
      return;
    }
    if (typing || location.hash === "#ferramentas") return;
    if (e.key === "ArrowDown" || e.key === "j") {
      e.preventDefault();
      moveSelection(1);
    } else if (e.key === "ArrowUp" || e.key === "k") {
      e.preventDefault();
      moveSelection(-1);
    }
  });
}

function moveSelection(delta) {
  if (!CURRENT_LEADS.length) return;
  const idx = CURRENT_LEADS.findIndex((l) => l.id === state.selectedId);
  const next = CURRENT_LEADS[Math.min(Math.max(idx + delta, 0), Math.min(CURRENT_LEADS.length, state.limit) - 1)];
  if (next) {
    selectLead(next.id, { scroll: true, overlay: false });
  }
}

/* ---------- motor, nichos ---------- */
async function loadHealthAndStats() {
  try {
    const data = await (await fetch("/api/health")).json();
    const badge = $("engine-badge");
    const online = !!(data.scraper_engine && data.scraper_engine.online);
    badge.textContent = online ? "Motor Google Maps ativo" : "Motor Google Maps desligado";
    badge.className = "engine " + (online ? "on" : "off");
    $("btn-queue-count").textContent = fmtInt((data.stats || {}).outreach_queue_ready ?? 0);
  } catch (err) {
    $("engine-badge").textContent = "Servidor sem resposta";
    $("engine-badge").className = "engine off";
  }
}

async function loadNiches() {
  ALL_NICHES = await (await fetch("/api/niches")).json();
  renderNichesGrid();
  const sel = $("filter-niche");
  sel.innerHTML =
    `<option value="">Todos os nichos</option>` + ALL_NICHES.map((n) => `<option value="${esc(n.slug)}">${esc(n.name)}</option>`).join("");
}

function renderNichesGrid() {
  $("niches-grid").innerHTML = ALL_NICHES.map((n) => {
    const offer = SERVICE_LONG[n.recommended_service || n.recommended_offer] || "";
    return `
      <label class="niche-chip">
        <input type="checkbox" value="${esc(n.slug)}" ${SELECTED_NICHES.has(n.slug) ? "checked" : ""} onchange="toggleNiche('${esc(n.slug)}', this.checked)" />
        <span><span class="niche-name">${esc(n.name)}</span><span class="niche-offer">${esc(offer)}</span></span>
      </label>`;
  }).join("");
}

function toggleNiche(slug, on) {
  if (on) SELECTED_NICHES.add(slug);
  else SELECTED_NICHES.delete(slug);
}

function selectAllNiches(all) {
  if (all) ALL_NICHES.forEach((n) => SELECTED_NICHES.add(n.slug));
  else SELECTED_NICHES.clear();
  renderNichesGrid();
}

/* ---------- busca real ---------- */
async function runSearchJob() {
  const city = $("input-city").value.trim() || "Piracicaba";
  const stateUf = ($("input-state").value.trim() || "SP").toUpperCase();
  const customKw = $("input-custom-kw").value.trim();
  const slugs = Array.from(SELECTED_NICHES);
  const fb = $("job-feedback");
  const btn = $("btn-run-job");

  if (!slugs.length && !customKw) {
    fb.className = "job-feedback err";
    fb.textContent = "Marque pelo menos um nicho.";
    return;
  }

  const started = Date.now();
  btn.disabled = true;
  fb.className = "job-feedback";
  const tick = () => {
    const s = Math.round((Date.now() - started) / 1000);
    btn.textContent = `Buscando… ${s} s`;
    fb.textContent = "Lendo o Google Maps e conferindo o site e o domínio de cada empresa. Pode levar cerca de 1 minuto.";
  };
  tick();
  const timer = setInterval(tick, 1000);

  try {
    const res = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        city,
        state: stateUf,
        niche_slugs: slugs,
        custom_keywords: customKw ? [customKw] : [],
        depth: parseInt($("input-depth").value || "5", 10),
        grid_size: 1,
        include_socials: true,
        run_xray: true,
        source_mode: $("input-source-mode").value || "auto",
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "A busca falhou.");
    SCOPE_CITY = city;
    state.tab = "ALL";
    state.limit = PAGE;
    state.selectedId = null;
    await Promise.all([loadHealthAndStats(), loadLeads()]);
    const secs = Math.round((Date.now() - started) / 1000);
    fb.className = "job-feedback ok";
    fb.textContent = `${fmtInt(data.total_leads_processed)} empresas reais em ${city} (${secs} s).`;
  } catch (err) {
    fb.className = "job-feedback err";
    fb.textContent = err.message;
  } finally {
    clearInterval(timer);
    btn.disabled = false;
    btn.textContent = "Buscar clientes reais";
  }
}

/* ---------- carga e filtros ---------- */
async function loadLeads() {
  try {
    const res = await fetch("/api/leads?limit=500");
    if (!res.ok) throw new Error("HTTP " + res.status);
    ALL_LEADS = await res.json();
  } catch (err) {
    renderError(err.message);
    return;
  }
  const typed = ($("input-city").value || "").trim().toLowerCase();
  const cities = {};
  ALL_LEADS.forEach((l) => (cities[l.city] = (cities[l.city] || 0) + 1));
  if (!SCOPE_CITY) {
    const match = Object.keys(cities).find((c) => c.toLowerCase() === typed);
    SCOPE_CITY = match || Object.keys(cities).sort((a, b) => cities[b] - cities[a])[0] || $("input-city").value.trim();
  }
  const first = ALL_LEADS.find((l) => l.city === SCOPE_CITY);
  if (first && first.state) {
    $("input-city").value = SCOPE_CITY;
    $("input-state").value = first.state;
  }
  applyFilters();
}

function onFilterChange() {
  state.limit = PAGE;
  applyFilters();
}

function scopeLeads() {
  return ALL_LEADS.filter((l) => !SCOPE_CITY || (l.city || "").toLowerCase() === SCOPE_CITY.toLowerCase());
}

function applyFilters() {
  const scope = scopeLeads();
  const q = ($("filter-search").value || "").trim().toLowerCase();
  const niche = $("filter-niche").value;
  const owner = $("filter-owner").value;
  const status = $("filter-status").value;
  const onlyWpp = $("filter-whatsapp").checked;
  const onlyDomain = $("filter-domain-free").checked;

  CURRENT_LEADS = scope
    .filter((l) => {
      if (state.tab !== "ALL" && offerOf(l) !== state.tab) return false;
      if (niche && l.niche_slug !== niche) return false;
      if (owner && l.assigned_to !== owner) return false;
      if (status && l.lead_status !== status) return false;
      if (onlyWpp && !waNumber(l)) return false;
      if (onlyDomain && !l.domain_available_br) return false;
      if (state.kpiNoSite && !hasNoSite(l)) return false;
      if (state.kpiContacted && !isContacted(l)) return false;
      if (q && !`${l.title} ${l.category} ${l.address}`.toLowerCase().includes(q)) return false;
      return true;
    })
    .sort((a, b) => (b.opportunity_score || 0) - (a.opportunity_score || 0) || (b.review_count || 0) - (a.review_count || 0));

  renderSummary(scope);
  renderRows();
  if (!CURRENT_LEADS.some((l) => l.id === state.selectedId)) {
    state.selectedId = CURRENT_LEADS[0] ? CURRENT_LEADS[0].id : null;
  }
  renderDetail();
}

function applyQuickTab(tab) {
  state.tab = tab;
  if (tab === "ALL") {
    state.kpiNoSite = false;
    state.kpiContacted = false;
    ["filter-whatsapp", "filter-domain-free"].forEach((id) => ($(id).checked = false));
    ["filter-niche", "filter-owner", "filter-status", "filter-search"].forEach((id) => ($(id).value = ""));
  }
  onFilterChange();
}

function kpiClick(key) {
  if (key === "nosite") state.kpiNoSite = !state.kpiNoSite;
  if (key === "contacted") state.kpiContacted = !state.kpiContacted;
  if (key === "wpp") $("filter-whatsapp").checked = !$("filter-whatsapp").checked;
  if (key === "domain") $("filter-domain-free").checked = !$("filter-domain-free").checked;
  onFilterChange();
}
function toggleDomainFreeFilter() {
  kpiClick("domain");
}

/* ---------- resumo ---------- */
function renderSummary(scope) {
  const total = scope.length;
  const noSite = scope.filter(hasNoSite).length;
  const wpp = scope.filter((l) => waNumber(l)).length;
  const dom = scope.filter((l) => l.domain_available_br).length;
  const contacted = scope.filter(isContacted).length;
  const offers = { SITE_NOVO: 0, REFORMA_SITE: 0, SISTEMA_COMPLEXO: 0 };
  scope.forEach((l) => offers[offerOf(l)]++);

  $("scope-label").textContent = scope.length ? `${SCOPE_CITY}, ${scope[0].state || ""}` : "Sem cidade";
  $("exec-summary-headline").textContent = total ? `Clientes em ${SCOPE_CITY}` : "Clientes";
  $("exec-summary-subtext").textContent = total
    ? `${fmtInt(noSite)} de ${fmtInt(total)} empresas não têm site próprio e ${fmtInt(dom)} têm o domínio .com.br livre. Comece pelas de maior chance.`
    : "Escolha os nichos na barra lateral e clique em Buscar clientes reais.";
  $("kpi-total").textContent = fmtInt(total);
  $("kpi-nosite").textContent = fmtInt(noSite);
  $("kpi-wpp").textContent = fmtInt(wpp);
  $("kpi-domain").textContent = fmtInt(dom);
  $("kpi-contacted").textContent = fmtInt(contacted);

  document.querySelectorAll("[data-count]").forEach((el) => {
    const k = el.dataset.count;
    el.textContent = k === "ALL" ? fmtInt(total) : fmtInt(offers[k] || 0);
  });
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === state.tab));
  const on = { nosite: state.kpiNoSite, wpp: $("filter-whatsapp").checked, domain: $("filter-domain-free").checked, contacted: state.kpiContacted };
  document.querySelectorAll("[data-kpi]").forEach((k) => k.classList.toggle("on", !!on[k.dataset.kpi]));
  const now = new Date();
  $("stamp").textContent = total ? `Atualizado ${now.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}` : "";
}

/* ---------- lista ---------- */
function renderSkeleton() {
  $("ready-reports-grid").innerHTML = Array.from({ length: 6 })
    .map(() => `<div class="skel"><i style="width:${40 + Math.round(Math.random() * 30)}%"></i></div>`)
    .join("");
}

function renderError(msg) {
  $("ready-reports-grid").innerHTML = `<div class="empty"><strong>Não foi possível carregar as empresas.</strong>${esc(msg)}<br/><button class="btn btn-sm" onclick="loadLeads()">Tentar de novo</button></div>`;
}

function shortAddress(addr) {
  const parts = String(addr || "").split(",").map((s) => s.trim());
  return parts.slice(0, 2).join(", ");
}

function renderRows() {
  const box = $("ready-reports-grid");
  const total = CURRENT_LEADS.length;
  const shown = Math.min(total, state.limit);
  $("list-total").textContent = total ? `1–${fmtInt(shown)} de ${fmtInt(total)}` : "0 empresas";
  $("btn-more").hidden = shown >= total;

  if (!scopeLeads().length) {
    box.innerHTML = `<div class="empty"><strong>Nenhuma empresa ainda.</strong>Marque os nichos na barra lateral e busque uma cidade.<br/><button class="btn btn-primary btn-sm" onclick="document.getElementById('input-city').focus()">Escolher cidade</button></div>`;
    return;
  }
  if (!total) {
    box.innerHTML = `<div class="empty"><strong>Nenhuma empresa neste filtro.</strong>Tire algum filtro para ver mais.<br/><button class="btn btn-sm" onclick="applyQuickTab('ALL')">Limpar filtros</button></div>`;
    return;
  }

  box.innerHTML = CURRENT_LEADS.slice(0, shown)
    .map((l) => {
      const offer = offerOf(l);
      const sel = l.id === state.selectedId;
      const rating = fmtRating(l.review_rating);
      const score = l.opportunity_score || 0;
      return `
      <div class="row ${sel ? "selected" : ""} ${isContacted(l) ? "contacted" : ""}" role="option" aria-selected="${sel}" tabindex="0" data-id="${l.id}"
           onclick="selectLead(${l.id}, {overlay:true})" onkeydown="if(event.key==='Enter'){selectLead(${l.id}, {overlay:true})}">
        <div style="min-width:0">
          <div class="name">${esc(l.title)}</div>
          <div class="sub2">${esc(l.category || "Empresa")} · ${l.review_count ? fmtInt(l.review_count) + " avaliações" : "sem avaliações"}</div>
        </div>
        <div><span class="pill ${PILL_CLASS[offer]}">${SERVICE_LABELS[offer]}</span></div>
        <div class="cell-r num cell-note">${rating ? esc(rating) : '<span class="dash">—</span>'}</div>
        <div class="cell-r num score cell-score ${score >= 85 ? "hi" : ""}">${score}</div>
      </div>`;
    })
    .join("");
}

function showMoreRows() {
  state.limit += PAGE;
  renderRows();
}

function selectLead(id, opts = {}) {
  state.selectedId = id;
  document.querySelectorAll(".row").forEach((r) => {
    const on = Number(r.dataset.id) === id;
    r.classList.toggle("selected", on);
    r.setAttribute("aria-selected", on);
    if (on && opts.scroll) r.scrollIntoView({ block: "nearest" });
  });
  renderDetail();
  if (opts.overlay && window.matchMedia("(max-width: 960px)").matches) {
    $("detail").classList.add("open");
  }
}

function closeDetailOverlay() {
  $("detail").classList.remove("open");
}

/* ---------- Central de Contato ---------- */
function renderDetail() {
  const body = $("detail-body");
  const l = CURRENT_LEADS.find((x) => x.id === state.selectedId) || ALL_LEADS.find((x) => x.id === state.selectedId);
  if (!l) {
    body.innerHTML = `<div class="d-empty"><strong>Central de Contato</strong>Escolha uma empresa na lista para ver o relatório e a mensagem pronta.</div>`;
    return;
  }
  const rr = readyReportOf(l);
  const sc = l.outreach_scripts || {};
  const offer = offerOf(l);
  const num = waNumber(l);
  const bullets = (rr.bullets || [])
    .map(
      (b) => `
      <div class="kv-row">
        <span class="kv-dot ${esc(b.status || "")}"></span>
        <div><div class="kv-k">${esc(b.label)}</div><div class="kv-v">${esc(b.text)}</div></div>
      </div>`
    )
    .join("");

  body.innerHTML = `
    <div class="d-section">
      <button class="btn btn-sm d-back" type="button" onclick="closeDetailOverlay()">Voltar para a lista</button>
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px">
        <h2 class="d-title">${esc(l.title)}</h2>
        <span class="pill ${PILL_CLASS[offer]}">${SERVICE_LABELS[offer]}</span>
      </div>
      <div class="d-meta">${esc(l.category || "Empresa")} · ${esc(shortAddress(l.address))}</div>
      <div class="d-meta">${l.phone ? esc(l.phone) : "Sem telefone"}${l.emails ? " · " + esc(l.emails) : ""}</div>
    </div>

    <div class="d-section">
      <div class="d-label">O que vender</div>
      <div class="sell"><span class="sell-what">${esc(rr.what_to_sell)}</span><span class="sell-ticket">${esc(rr.ticket_range)}</span></div>
      ${rr.executive_pitch ? `<p class="sell-pitch">${esc(rr.executive_pitch)}</p>` : ""}
    </div>

    ${bullets ? `<div class="d-section"><div class="d-label">O que descobrimos</div><div class="kv">${bullets}</div></div>` : ""}

    <div class="d-section">
      <div class="d-label"><span>Mensagem pronta</span><span class="copied" id="copied-${l.id}"></span></div>
      <textarea id="card-wpp-${l.id}" aria-label="Mensagem para enviar">${esc(sc.whatsapp || "")}</textarea>
      <div class="d-actions">
        ${
          num
            ? `<button class="btn btn-primary" type="button" onclick="openWhatsApp(${l.id})">Chamar no WhatsApp</button>`
            : `<button class="btn" type="button" disabled title="Sem telefone com DDD">Sem WhatsApp</button>`
        }
        <button class="btn" type="button" onclick="copyCardMessage(${l.id})">Copiar mensagem</button>
        <button class="btn" type="button" onclick="enqueueSingleLead(${l.id}, 'whatsapp')">Guardar na fila do robô</button>
      </div>
      <div class="d-actions">
        <button class="btn btn-sm" type="button" onclick="openLeadModal(${l.id})">E-mail, Instagram e raio-x completo</button>
      </div>
    </div>

    <div class="d-section">
      <div class="d-grid2">
        <label class="field"><span>Responsável</span>
          <select onchange="updateLeadOwnerOrStatus(${l.id}, {assigned_to: this.value})">
            <option value="nao_atribuido" ${l.assigned_to === "nao_atribuido" ? "selected" : ""}>Sem responsável</option>
            <option value="eu" ${l.assigned_to === "eu" ? "selected" : ""}>Eu</option>
            <option value="amigo" ${l.assigned_to === "amigo" ? "selected" : ""}>Meu amigo</option>
          </select></label>
        <label class="field"><span>Situação</span>
          <select onchange="updateLeadOwnerOrStatus(${l.id}, {lead_status: this.value})">
            ${[["novo", "Novo"], ["analisado", "Analisado"], ["contatado", "Já chamei"], ["respondeu", "Respondeu"], ["reuniao", "Reunião"], ["fechado", "Fechado"], ["descartado", "Descartado"]]
              .map(([v, t]) => `<option value="${v}" ${l.lead_status === v ? "selected" : ""}>${t}</option>`)
              .join("")}
          </select></label>
      </div>
    </div>`;
}

function openWhatsApp(id) {
  const l = ALL_LEADS.find((x) => x.id === id);
  if (!l) return;
  const msg = ($(`card-wpp-${id}`) || {}).value || "";
  window.open(`https://wa.me/${waNumber(l)}?text=${encodeURIComponent(msg)}`, "_blank", "noopener");
  markLeadContacted(id);
}

function copyCardMessage(id) {
  const el = $(`card-wpp-${id}`);
  if (!el) return;
  navigator.clipboard.writeText(el.value).then(() => {
    const fb = $(`copied-${id}`);
    if (fb) {
      fb.textContent = "Copiado";
      setTimeout(() => (fb.textContent = ""), 2000);
    }
  });
}

async function updateLeadOwnerOrStatus(leadId, patch) {
  const res = await fetch(`/api/leads/${leadId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (res.ok) {
    const l = ALL_LEADS.find((x) => x.id === leadId);
    if (l) Object.assign(l, patch);
    renderSummary(scopeLeads());
    renderRows();
  }
}

async function markLeadContacted(leadId) {
  const l = ALL_LEADS.find((x) => x.id === leadId);
  if (l && (l.lead_status === "novo" || l.lead_status === "analisado")) {
    await updateLeadOwnerOrStatus(leadId, { lead_status: "contatado" });
    renderDetail();
  }
}

/* ---------- fila do robô ---------- */
async function enqueueSingleLead(leadId, channel) {
  const res = await fetch("/api/outreach/enqueue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lead_ids: [leadId], channels: [channel] }),
  });
  const data = await res.json().catch(() => ({}));
  await loadHealthAndStats();
  const fb = $(`copied-${leadId}`);
  if (fb) {
    fb.textContent = data.enqueued_count ? "Guardado na fila" : "Já estava na fila";
    setTimeout(() => (fb.textContent = ""), 2500);
  }
}

async function enqueueSelectedLeads(channel) {
  const ids = CURRENT_LEADS.filter((l) => waNumber(l)).map((l) => l.id);
  if (!ids.length) {
    alert("Nenhuma empresa com WhatsApp neste filtro.");
    return;
  }
  if (!confirm(`Guardar ${ids.length} empresas com WhatsApp na fila do robô?`)) return;
  const res = await fetch("/api/outreach/enqueue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lead_ids: ids, channels: [channel] }),
  });
  const data = await res.json();
  await loadHealthAndStats();
  alert(`${data.enqueued_count} guardadas na fila do robô.`);
}

async function openQueueModal() {
  const items = await (await fetch("/api/outreach/queue")).json();
  const body = $("queue-modal-body");
  if (!items.length) {
    body.innerHTML = `<div class="empty"><strong>A fila está vazia.</strong>Use “Guardar na fila do robô” na Central de Contato de uma empresa.</div>`;
  } else {
    body.innerHTML = `
      <table class="table-leads">
        <thead><tr><th>Empresa</th><th>Canal</th><th>Situação</th><th>Mensagem</th></tr></thead>
        <tbody>${items
          .map(
            (it) => `<tr>
              <td><strong>${esc(it.lead_title || "Empresa #" + it.lead_id)}</strong><br/><span class="meta">${esc(it.lead_city || "")}</span></td>
              <td>${esc(it.channel)}<br/><span class="meta">${esc(it.recipient)}</span></td>
              <td><span class="pain-tag">${esc(it.status)}</span></td>
              <td style="white-space:pre-wrap;max-width:420px">${esc(it.message_body)}</td></tr>`
          )
          .join("")}</tbody>
      </table>`;
  }
  $("queue-modal").classList.add("open");
}
function closeQueueModal() {
  $("queue-modal").classList.remove("open");
}

/* ---------- dossiê completo ---------- */
async function openLeadModal(leadId) {
  const l = await (await fetch(`/api/leads/${leadId}`)).json();
  const sc = l.outreach_scripts || {};
  const rr = readyReportOf(l);
  const rep = (l.external_tools_links || {}).embedded_reports || {};
  const bw = rep.builtwith || {};
  const wp = rep.wappalyzer || {};
  const wc = rep.whatcms || {};
  const dns = rep.dns_ssl || {};
  const missing = (wc.missing_systems_opportunities || []).map((o) => `<li>${esc(o)}</li>`).join("");

  $("modal-lead-title").textContent = l.title;
  $("modal-lead-subtitle").textContent = `${rr.what_to_sell} · ${rr.ticket_range} · ${l.phone || "sem telefone"}`;

  const cell = (title, html) => `<div class="embedded-box" style="margin-top:0"><strong>${title}</strong><br/>${html}</div>`;
  $("modal-lead-body").innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:24px">
      <div>
        <div class="section-bar">Diagnóstico técnico</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          ${cell("google.com/maps", `Nota ${esc(fmtRating(l.review_rating) || "—")} (${fmtInt(l.review_count)} avaliações)<br/>${esc(l.category || "")}`)}
          ${cell("casadosdados / CNPJ", `CNPJ: ${esc(l.cnpj || "não informado")}<br/>Abertura: ${esc(l.opened_date || "não informada")}`)}
          ${cell("registro.br", `${esc(l.suggested_domain)}<br/><strong>${l.domain_available_br ? "Livre para registro" : "Já registrado"}</strong>`)}
          ${cell("downforeveryoneorjustme.com", `${l.has_website ? (l.site_in_air ? "Online (HTTP " + esc(l.http_status) + ")" : "Fora do ar") : "Sem site"}<br/>IP ${esc(dns.resolved_ip || "—")} · ${esc(l.response_time_ms || 0)} ms<br/>${l.has_ssl ? "HTTPS ativo" : "Sem HTTPS"}`)}
          ${cell("builtwith.com", `Servidor: ${esc(bw.server || "—")}<br/>Pixels: ${esc((bw.analytics_pixels || []).join(", ") || "nenhum")}<br/>Chat: ${esc((bw.chat_widgets || []).join(", ") || "nenhum")}`)}
          ${cell("wappalyzer.com", `JS: ${esc((wp.js_frameworks || []).join(", ") || "—")}<br/>CSS: ${esc((wp.css_ui || []).join(", ") || "—")}<br/>${l.is_mobile_friendly ? "Responsivo no celular" : "Não responsivo"}`)}
          ${cell("whatcms.org", `CMS: <strong>${esc(l.detected_cms || "—")}</strong><br/>Sistema integrado: ${l.has_complex_system ? "sim" : "não"}${missing ? `<ul style="margin:4px 0 0;padding-left:16px">${missing}</ul>` : ""}`)}
          ${cell("web.archive.org", `1ª captura: ${esc(l.wayback_first_seen || "sem arquivo")}<br/>Última: ${esc(l.wayback_last_seen || "sem arquivo")}<br/>Parado há: ${l.wayback_days_since_update != null ? esc(l.wayback_days_since_update) + " dias" : "—"}`)}
        </div>
      </div>
      <div>
        <div class="section-bar">Mensagens prontas</div>
        <div class="tool-card" style="margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px"><strong>WhatsApp</strong>
            <button class="btn btn-sm" onclick="copyText('modal-wpp-text')">Copiar</button></div>
          <textarea id="modal-wpp-text" rows="5">${esc(sc.whatsapp || "")}</textarea>
        </div>
        <div class="tool-card" style="margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px"><strong>Instagram Direct</strong>
            <span style="display:flex;gap:6px"><button class="btn btn-sm" onclick="copyText('modal-ig-text')">Copiar</button>
            ${l.instagram ? `<button class="btn btn-sm" onclick="window.open('${esc(l.instagram)}','_blank','noopener')">Abrir perfil</button>` : ""}</span></div>
          <textarea id="modal-ig-text" rows="3">${esc(sc.instagram_dm || "")}</textarea>
        </div>
        <div class="tool-card">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px"><strong>E-mail — ${esc(sc.email_subject || "")}</strong>
            <span style="display:flex;gap:6px"><button class="btn btn-sm" onclick="copyText('modal-email-text')">Copiar</button>
            ${sc.mailto_url ? `<button class="btn btn-sm" onclick="window.location.href=${JSON.stringify(sc.mailto_url).replace(/"/g, "&quot;")}">Abrir e-mail</button>` : ""}</span></div>
          <textarea id="modal-email-text" rows="4">${esc(sc.email_body || "")}</textarea>
        </div>
      </div>
    </div>`;
  $("lead-modal").classList.add("open");
}
function closeLeadModal() {
  $("lead-modal").classList.remove("open");
}
function copyText(id) {
  const el = $(id);
  if (el) navigator.clipboard.writeText(el.value);
}

/* ---------- cadastro manual e CSV ---------- */
function openManualLeadModal() {
  $("manual-modal-title").textContent = "Adicionar empresa";
  $("manual-modal-body").innerHTML = `
    <div style="display:flex;flex-direction:column;gap:10px">
      <input id="m-title" placeholder="Nome da empresa" />
      <input id="m-city" value="${esc($("input-city").value || "")}" placeholder="Cidade" />
      <input id="m-phone" placeholder="Telefone ou WhatsApp com DDD" />
      <input id="m-website" placeholder="Site atual (vazio se não tiver)" />
      <input id="m-email" placeholder="E-mail (opcional)" />
      <button class="btn btn-primary" onclick="submitManualLead()">Gerar relatório desta empresa</button>
    </div>`;
  $("manual-modal").classList.add("open");
}
function openCsvImportModal() {
  $("manual-modal-title").textContent = "Importar lista CSV";
  $("manual-modal-body").innerHTML = `
    <div style="display:flex;flex-direction:column;gap:10px">
      <p class="meta">Cole o CSV com cabeçalho <code>title,phone,emails,website,category,address,review_rating,review_count</code>.</p>
      <textarea id="csv-paste-area" rows="8" style="font-family:var(--mono);font-size:12px"></textarea>
      <button class="btn btn-primary" onclick="submitCsvImport()">Importar e gerar relatórios</button>
    </div>`;
  $("manual-modal").classList.add("open");
}
function closeManualModal() {
  $("manual-modal").classList.remove("open");
}
async function submitManualLead() {
  const title = $("m-title").value.trim();
  if (!title) return;
  await fetch("/api/leads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      city: $("m-city").value.trim() || SCOPE_CITY,
      phone: $("m-phone").value.trim(),
      website: $("m-website").value.trim(),
      emails: $("m-email").value.trim(),
      run_xray: true,
    }),
  });
  closeManualModal();
  await loadLeads();
}
async function submitCsvImport() {
  const csvText = $("csv-paste-area").value.trim();
  if (!csvText) return;
  await fetch("/api/leads/import-csv", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ csv_text: csvText, city: $("input-city").value.trim() || SCOPE_CITY, state: $("input-state").value.trim() || "SP", run_xray: true }),
  });
  closeManualModal();
  await loadLeads();
}

/* ============================================================
   FERRAMENTAS (os oito motores, embutidos — nenhum link externo)
   ============================================================ */
async function runEmbeddedMapsEngineCheck() {
  const box = $("embedded-maps-box");
  if (!box) return;
  const city = ($("input-city").value || "Piracicaba").trim();
  const st = ($("input-state").value || "SP").trim();
  try {
    const data = await (await fetch(`/api/tools/maps-engine?city=${encodeURIComponent(city)}&state=${encodeURIComponent(st)}&grid_size=2`)).json();
    const eng = data.engine || {};
    const geo = data.geocoding || {};
    box.innerHTML = `
      <span class="embedded-pill ${eng.online ? "ok" : "warn"}">${eng.online ? "Container ativo" : "Container desligado"} · ${esc(eng.base_url)}</span>
      <span class="embedded-pill">${esc(geo.city)}-${esc(geo.state)}: ${esc(geo.lat)}, ${esc(geo.lon)}</span>
      <span class="embedded-pill">${esc(geo.cells_count)} quadrantes</span>`;
  } catch (err) {
    box.innerHTML = `<span class="embedded-pill err">Erro ao consultar o motor: ${esc(err.message)}</span>`;
  }
}

async function startDockerEngineEmbedded() {
  const box = $("embedded-maps-box");
  if (box) box.textContent = "Iniciando o container gmaps-scraper…";
  try {
    await fetch("/api/engine/start", { method: "POST" });
    await Promise.all([loadHealthAndStats(), runEmbeddedMapsEngineCheck()]);
  } catch (err) {
    if (box) box.innerHTML = `<span class="embedded-pill err">Falha ao iniciar: ${esc(err.message)}</span>`;
  }
}

async function runEmbeddedCnpjLookup(importLead = false) {
  const input = ($("embedded-cnpj-input").value || "").trim();
  const box = $("casadosdados-box");
  if (!input) {
    box.textContent = "Digite um CNPJ com 14 números.";
    return;
  }
  box.textContent = "Consultando a Receita Federal…";
  try {
    const niche = Array.from(SELECTED_NICHES)[0] || "geral";
    const res = await fetch(`/api/tools/cnpj?cnpj=${encodeURIComponent(input)}&import_as_lead=${importLead}&niche_slug=${encodeURIComponent(niche)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "CNPJ inválido");
    const c = data.cnpj_data;
    const socios = (c.qsa || []).map((s) => `${esc(s.nome_socio)} (${esc(s.qualificacao_socio)})`).join(" · ");
    box.innerHTML = `
      <strong>${esc(c.nome_fantasia || c.razao_social)}</strong> <span class="embedded-pill ok">${esc(c.situacao_cadastral)}</span>
      <span class="embedded-pill">Abertura ${esc(c.data_inicio_atividade || "N/D")}</span><br/>
      ${esc(c.razao_social)} · ${esc(c.cnpj_formatted)}<br/>
      CNAE: ${esc(c.cnae_fiscal)} — ${esc(c.cnae_fiscal_descricao)}<br/>
      Sócios: ${socios || "não informado"}<br/>
      Contato: ${esc(c.telefone || "sem telefone")} · ${esc(c.email || "sem e-mail")} · ${esc(c.municipio)}-${esc(c.uf)}<br/>
      <button class="btn btn-sm" style="margin-top:8px" onclick="runEmbeddedCnpjLookup(true)">Gerar relatório para este CNPJ</button>`;
    if (data.imported_lead) await loadLeads();
  } catch (err) {
    box.innerHTML = `<span class="embedded-pill err">${esc(err.message)}</span>`;
  }
}

function renderRegistroBrBox(data) {
  const out = $("quick-domain-result");
  if (!out || !data) return;
  if (data.available) {
    out.innerHTML = `<span class="embedded-pill ok">Livre no Registro.br: ${esc(data.domain)}</span>`;
  } else {
    out.innerHTML = `<span class="embedded-pill warn">Já registrado: ${esc(data.domain)}</span>
      ${data.owner_name ? `<span class="embedded-pill">Titular: ${esc(data.owner_name)}</span>` : ""}
      ${data.created_at ? `<span class="embedded-pill">Criado ${esc(data.created_at)}</span>` : ""}
      ${data.expires_at ? `<span class="embedded-pill">Expira ${esc(data.expires_at)}</span>` : ""}`;
  }
}

async function checkQuickDomain(customQuery) {
  const inputEl = $("quick-domain-input");
  const query = (customQuery || inputEl.value || "").trim();
  const out = $("quick-domain-result");
  if (!query) return;
  if (customQuery) inputEl.value = customQuery;
  out.textContent = "Consultando o RDAP do Registro.br…";
  try {
    const city = ($("input-city").value || "").trim();
    renderRegistroBrBox(await (await fetch(`/api/tools/registro-br?query=${encodeURIComponent(query)}&city=${encodeURIComponent(city)}`)).json());
  } catch (e) {
    out.innerHTML = `<span class="embedded-pill err">Erro: ${esc(e.message)}</span>`;
  }
}

function renderSiteHealthBox(data) {
  const box = $("quick-health-result");
  if (!box || !data) return;
  const cls = data.site_in_air ? (data.has_ssl ? "ok" : "warn") : "err";
  const title = !data.has_website ? "Sem site cadastrado" : data.site_in_air ? `Online (HTTP ${esc(data.http_status)} · ${esc(data.response_time_ms)} ms)` : `Fora do ar (${esc(data.verdict || "erro")})`;
  box.innerHTML = `
    <span class="embedded-pill ${cls}">${title}</span>
    <span class="embedded-pill">IP: ${esc(data.resolved_ip || (data.dns_ok ? "resolvido" : "sem host"))}</span>
    <span class="embedded-pill ${data.has_ssl ? "ok" : "warn"}">${data.has_ssl ? "HTTPS válido" : "Sem HTTPS"}</span>`;
}

async function runEmbeddedSiteHealth(customUrl) {
  const inputEl = $("quick-health-input");
  const url = (customUrl || inputEl.value || "").trim();
  const box = $("quick-health-result");
  if (!url) return;
  box.textContent = "Testando DNS, SSL e resposta do servidor…";
  try {
    renderSiteHealthBox(await (await fetch(`/api/tools/site-health?url=${encodeURIComponent(url)}`)).json());
  } catch (err) {
    box.innerHTML = `<span class="embedded-pill err">Erro: ${esc(err.message)}</span>`;
  }
}

function renderAll4RightColumnScanners(reports, leadOrXray, targetLabel) {
  const bw = reports.builtwith || {};
  const wp = reports.wappalyzer || {};
  const wc = reports.whatcms || {};
  const wb = reports.wayback || {};
  ["builtwith", "wappalyzer", "whatcms", "wayback"].forEach((id) => {
    const lbl = $(`${id}-target-label`);
    if (lbl) lbl.textContent = targetLabel || "Analisado";
  });
  const pills = (arr, empty, cls = "ok") => (arr && arr.length ? arr.map((p) => `<span class="embedded-pill ${cls}">${esc(p)}</span>`).join("") : `<span class="embedded-pill warn">${empty}</span>`);

  $("embedded-builtwith-box").innerHTML = `
    <span class="embedded-pill">Servidor: ${esc(bw.server || "não detectado")}</span><span class="embedded-pill">CDN: ${esc(bw.cdn || "nenhuma")}</span><br/>
    Pixels: ${pills(bw.analytics_pixels, "sem pixel de anúncios")}<br/>Conversão: ${pills(bw.chat_widgets, "sem botão de WhatsApp ou chat")}`;

  const seo = wp.seo_meta || {};
  $("embedded-wappalyzer-box").innerHTML = `
    JS: ${pills(wp.js_frameworks, "nenhum framework", "")}<br/>CSS: ${pills(wp.css_ui, "CSS padrão", "")}<br/>
    <span class="embedded-pill ${seo.is_mobile_viewport ? "ok" : "err"}">${seo.is_mobile_viewport ? "Responsivo no celular" : "Sem viewport mobile"}</span>`;

  const opps = (wc.missing_systems_opportunities || []).map((o) => `<li>${esc(o)}</li>`).join("");
  $("embedded-whatcms-box").innerHTML = `
    <span class="embedded-pill ${wc.cms_name === "Sem Site" || wc.cms_name === "Wix" ? "warn" : "ok"}">CMS: ${esc(wc.cms_name || leadOrXray.detected_cms || "desconhecido")}</span>
    <span class="embedded-pill ${wc.has_complex_system ? "ok" : "warn"}">${wc.has_complex_system ? "Tem sistema integrado" : "Sem agendamento ou portal"}</span>
    ${opps ? `<ul style="margin:6px 0 0;padding-left:18px">${opps}</ul>` : ""}`;

  const days = wb.wayback_days_since_update ?? leadOrXray.wayback_days_since_update;
  $("embedded-wayback-box").innerHTML = `
    <span class="embedded-pill ${days && days > 365 ? "warn" : "ok"}">${days != null ? `${esc(days)} dias desde a última captura` : "Sem capturas"}</span>
    <span class="embedded-pill">1ª: ${esc(wb.wayback_first_seen || leadOrXray.wayback_first_seen || "—")}</span>
    <span class="embedded-pill">Última: ${esc(wb.wayback_last_seen || leadOrXray.wayback_last_seen || "—")}</span>`;
}

async function runEmbeddedFullXrayInput() {
  const url = ($("quick-xray-url").value || "").trim();
  if (!url) return;
  $("embedded-builtwith-box").textContent = `Rodando o raio-x em ${url}…`;
  try {
    const city = ($("input-city").value || "").trim();
    const xray = await (await fetch(`/api/tools/site-xray?url=${encodeURIComponent(url)}&company_name=${encodeURIComponent(url)}&city=${encodeURIComponent(city)}`)).json();
    const reports = (xray.external_tools_links || {}).embedded_reports || {};
    renderRegistroBrBox(reports.registro_br);
    renderSiteHealthBox({ has_website: xray.has_website, site_in_air: xray.site_in_air, http_status: xray.http_status, has_ssl: xray.has_ssl, response_time_ms: xray.response_time_ms, ...(reports.dns_ssl || {}) });
    renderAll4RightColumnScanners(reports, xray, url);
  } catch (err) {
    $("embedded-builtwith-box").innerHTML = `<span class="embedded-pill err">Erro: ${esc(err.message)}</span>`;
  }
}

function populateEmbeddedToolsFromLead(lead) {
  if (!lead) return;
  const reports = (lead.external_tools_links || {}).embedded_reports || {};
  $("quick-domain-input").value = lead.suggested_domain || lead.title || "";
  $("quick-health-input").value = lead.website || "";
  $("quick-xray-url").value = lead.website || "";
  if (lead.cnpj) $("embedded-cnpj-input").value = lead.cnpj;
  if (reports.registro_br) renderRegistroBrBox(reports.registro_br);
  renderSiteHealthBox({ has_website: lead.has_website, site_in_air: lead.site_in_air, http_status: lead.http_status, has_ssl: lead.has_ssl, response_time_ms: lead.response_time_ms, ...(reports.dns_ssl || {}) });
  renderAll4RightColumnScanners(reports, lead, lead.title);
}

window.addEventListener("DOMContentLoaded", initDashboard);
