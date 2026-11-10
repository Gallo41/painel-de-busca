/* Painel de Busca — front-end (lista + central de contato).
   Dados vêm de /api/leads (reais, do motor Google Maps em Docker). Filtros rodam no navegador: instantâneos. */

let ALL_NICHES = [];
let SELECTED_NICHES = new Set(["clinicas-odontologicas", "escritorios-advocacia", "imobiliarias-corretores"]);
let ALL_LEADS = [];
let CURRENT_LEADS = [];
let SCOPE_CITY = "";
const SAVED_PAGE_SIZE = parseInt(localStorage.getItem("painel_page_size") || "5", 10);
const DEFAULT_PAGE_SIZE = [5, 8, 10, 15, 20].includes(SAVED_PAGE_SIZE) ? SAVED_PAGE_SIZE : 5;
const PAGE = DEFAULT_PAGE_SIZE;
const state = {
  tab: "ALL",
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  limit: DEFAULT_PAGE_SIZE,
  selectedId: null,
  kpiNoSite: false,
  kpiContacted: false,
  isPrinting: false,
};

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
const waNumber = (l) => (((l.outreach_scripts || {}).automation_payload || {}).whatsapp_number || l.whatsapp_clean || l.phone || "").trim();
const isContacted = (l) => ["contatado", "respondeu", "reuniao", "fechado", "fazendo", "vou_fazer"].includes(l.lead_status);

function normStatus(s) {
  if (s === "vou_fazer") return "vou-fazer";
  if (s === "fazendo" || s === "contatado" || s === "respondeu" || s === "reuniao") return "fazendo";
  if (s === "nao_fazer" || s === "descartado") return "nao-fazer";
  if (s === "fechado") return "fechado";
  return "novo";
}

function labelStatus(s) {
  const norm = normStatus(s);
  if (norm === "vou-fazer") return "🎯 Vou fazer";
  if (norm === "fazendo") return "⏳ Fazendo";
  if (norm === "nao-fazer") return "❌ Não fazer";
  if (norm === "fechado") return "✅ Fechado";
  return "⚪ Novo";
}

function readyReportOf(l) {
  const rr = (l.outreach_scripts || {}).ready_report;
  if (rr && Array.isArray(rr.bullets)) return rr;
  const offer = offerOf(l);
  return {
    what_to_sell: SERVICE_LONG[offer],
    ticket_range: offer === "SISTEMA_COMPLEXO" ? "R$ 1.800 a R$ 3.800" : offer === "REFORMA_SITE" ? "R$ 1.100 a R$ 2.000" : "R$ 600 a R$ 1.500",
    executive_pitch: l.pain_summary || "",
    bullets: [],
  };
}

/* ---------- tema e inicialização ---------- */
function initTheme() {
  const saved = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  try {
    localStorage.setItem("theme", next);
  } catch (e) {}
}

initTheme();

async function initDashboard() {
  initTheme();
  bindShortcuts();
  renderSkeleton();
  await Promise.all([loadHealthAndStats(), loadNiches()]);
  await loadLeads();
  window.addEventListener("hashchange", routeFromHash);
  window.addEventListener("beforeprint", () => {
    state.isPrinting = true;
    renderRows();
  });
  window.addEventListener("afterprint", () => {
    state.isPrinting = false;
    renderRows();
  });
  routeFromHash();
}

function routeFromHash() {
  const hash = location.hash;
  let view = "clientes";
  if (hash === "#ferramentas") view = "ferramentas";
  else if (hash === "#agente" || hash === "#fila") view = "agente";
  else if (hash === "#analise") view = "analise";

  if ($("view-clientes")) $("view-clientes").hidden = view !== "clientes";
  if ($("view-ferramentas")) $("view-ferramentas").hidden = view !== "ferramentas";
  if ($("view-agente")) $("view-agente").hidden = view !== "agente";
  if ($("view-analise")) $("view-analise").hidden = view !== "analise";

  document.querySelectorAll("[data-nav]").forEach((a) => {
    if (a.dataset.nav === view) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  $("sidebar").classList.remove("open");
  if (view === "ferramentas") {
    const lead = ALL_LEADS.find((x) => x.id === state.selectedId) || CURRENT_LEADS[0];
    runEmbeddedMapsEngineCheck();
    if (lead) populateEmbeddedToolsFromLead(lead);
  } else if (view === "agente") {
    renderAgentDashboardView();
  } else if (view === "analise" && typeof loadAnalysis === "function") {
    loadAnalysis();
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
    if (typing || (location.hash && location.hash !== "#clientes")) return;
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
  const startIdx = (state.page - 1) * state.pageSize;
  const endIdx = Math.min(startIdx + state.pageSize, CURRENT_LEADS.length);
  const pageLeads = CURRENT_LEADS.slice(startIdx, endIdx);
  if (!pageLeads.length) return;

  const idx = pageLeads.findIndex((l) => l.id === state.selectedId);
  if (idx === -1) {
    selectLead(pageLeads[0].id, { scroll: true, overlay: false });
    return;
  }

  const nextIdx = idx + delta;
  if (nextIdx >= 0 && nextIdx < pageLeads.length) {
    selectLead(pageLeads[nextIdx].id, { scroll: true, overlay: false });
  } else if (nextIdx < 0 && state.page > 1) {
    goToPage(state.page - 1);
    const prevStart = (state.page - 1) * state.pageSize;
    const prevLeads = CURRENT_LEADS.slice(prevStart, prevStart + state.pageSize);
    if (prevLeads.length) {
      selectLead(prevLeads[prevLeads.length - 1].id, { scroll: true, overlay: false });
    }
  } else if (nextIdx >= pageLeads.length && state.page < Math.ceil(CURRENT_LEADS.length / state.pageSize)) {
    goToPage(state.page + 1);
    const nextStart = (state.page - 1) * state.pageSize;
    const nextLeads = CURRENT_LEADS.slice(nextStart, Math.min(nextStart + state.pageSize, CURRENT_LEADS.length));
    if (nextLeads.length) {
      selectLead(nextLeads[0].id, { scroll: true, overlay: false });
    }
  }
}

/* ---------- motor, nichos ---------- */
async function loadHealthAndStats() {
  try {
    const data = await (await fetch("/api/health")).json();
    const badge = $("engine-badge");
    const dot = $("status-pulse-dot");
    const online = !!(data.scraper_engine && data.scraper_engine.online);
    if (badge) {
      badge.textContent = online ? "Motor Maps ativo" : "Motor Maps desligado";
      badge.className = "status-title engine " + (online ? "on" : "off");
    }
    if (dot) dot.className = "status-pulse-dot " + (online ? "on" : "off");

    const totalLeads = (data.stats || {}).total_leads ?? 0;
    const leadsEl = $("sidebar-total-leads");
    if (leadsEl) leadsEl.textContent = `${fmtInt(totalLeads)} empresas`;

    const qReady = (data.stats || {}).outreach_queue_ready ?? 0;
    if ($("btn-queue-count")) $("btn-queue-count").textContent = fmtInt(qReady);
    if ($("agent-banner-queue-count")) $("agent-banner-queue-count").textContent = fmtInt(qReady);

    fetch("/api/agent/settings")
      .then((r) => r.json())
      .then((bundle) => {
        const st = bundle.settings || {};
        const modeEl = $("agent-banner-mode");
        if (modeEl) {
          if (st.test_mode) {
            modeEl.textContent = `Modo Teste: +${st.test_client_phone || "5519996109028"}`;
            modeEl.className = "agent-test-pill";
          } else {
            modeEl.textContent = "Modo Produção: Disparos Reais";
            modeEl.className = "agent-test-pill mode-prod";
          }
        }
        const bossEl = $("agent-banner-boss");
        if (bossEl) {
          bossEl.textContent = `Chefe: +${st.boss_phone || "551999958516"}`;
        }
      })
      .catch(() => {});
  } catch (err) {
    if ($("engine-badge")) {
      $("engine-badge").textContent = "Servidor offline";
      $("engine-badge").className = "status-title engine off";
    }
    if ($("status-pulse-dot")) $("status-pulse-dot").className = "status-pulse-dot off";
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
    const offerKey = n.recommended_service || n.recommended_offer || "SITE_NOVO";
    const shortLabel = SERVICE_LABELS[offerKey] || "Site novo";
    const pillClass = PILL_CLASS[offerKey] || "site";
    const checked = SELECTED_NICHES.has(n.slug);
    return `
      <label class="niche-chip ${checked ? "is-selected" : ""}" data-slug="${esc(n.slug)}">
        <input type="checkbox" value="${esc(n.slug)}" ${checked ? "checked" : ""} onchange="toggleNiche('${esc(n.slug)}', this.checked, this)" />
        <div class="niche-info">
          <div class="niche-name">${esc(n.name)}</div>
          <div class="niche-meta">
            <span class="niche-badge badge-${pillClass}">${esc(shortLabel)}</span>
          </div>
        </div>
      </label>`;
  }).join("");
}

function toggleNiche(slug, on, el) {
  if (on) SELECTED_NICHES.add(slug);
  else SELECTED_NICHES.delete(slug);
  if (el) {
    const parent = el.closest(".niche-chip");
    if (parent) parent.classList.toggle("is-selected", on);
  }
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
    btn.innerHTML = `<span>Buscando… ${s} s</span>`;
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
    state.page = 1;
    state.limit = state.pageSize;
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
    btn.innerHTML = `<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10.5 10.5L14 14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span>Buscar clientes reais</span>`;
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
  state.page = 1;
  applyFilters();
}

function onInlineSearch(val) {
  const topSearch = $("filter-search");
  if (topSearch && topSearch.value !== val) {
    topSearch.value = val;
  }
  onFilterChange();
}

function setStatusFilter(key) {
  state.statusFilter = key;
  const selectStatus = $("filter-status");
  if (selectStatus) selectStatus.value = key;
  document.querySelectorAll(".decision-pill-btn").forEach((btn) => {
    btn.classList.toggle("active", (btn.dataset.statusFilter || "") === key);
  });
  onFilterChange();
}

function clearAllFilters() {
  state.statusFilter = "";
  state.tab = "ALL";
  state.kpiNoSite = false;
  state.kpiContacted = false;
  ["filter-whatsapp", "filter-domain-free", "filter-hide-ignored"].forEach((id) => {
    const el = $(id);
    if (el) el.checked = false;
  });
  ["filter-niche", "filter-owner", "filter-status", "filter-search", "filter-search-inline"].forEach((id) => {
    const el = $(id);
    if (el) el.value = "";
  });
  document.querySelectorAll(".decision-pill-btn").forEach((btn) => {
    btn.classList.toggle("active", (btn.dataset.statusFilter || "") === "");
  });
  onFilterChange();
}

function scopeLeads() {
  return ALL_LEADS.filter((l) => !SCOPE_CITY || (l.city || "").toLowerCase() === SCOPE_CITY.toLowerCase());
}

function applyFilters() {
  const scope = scopeLeads();
  const topSearch = $("filter-search");
  const inlineSearch = $("filter-search-inline");
  const q = ((inlineSearch ? inlineSearch.value : "") || (topSearch ? topSearch.value : "")).trim().toLowerCase();
  if (topSearch && inlineSearch && topSearch.value !== inlineSearch.value) {
    if (document.activeElement === inlineSearch) topSearch.value = inlineSearch.value;
    else if (document.activeElement === topSearch) inlineSearch.value = topSearch.value;
  }
  const niche = $("filter-niche").value;
  const owner = $("filter-owner").value;
  const status = state.statusFilter !== undefined && state.statusFilter !== "" ? state.statusFilter : $("filter-status").value;
  const hideIgnored = $("filter-hide-ignored") ? $("filter-hide-ignored").checked : false;
  const onlyWpp = $("filter-whatsapp").checked;
  const onlyDomain = $("filter-domain-free").checked;

  const hasActiveFilters = Boolean(
    q || niche || owner || status || onlyWpp || onlyDomain || hideIgnored || state.tab !== "ALL" || state.kpiNoSite || state.kpiContacted
  );
  const btnClear = $("btn-clear-filters");
  if (btnClear) btnClear.style.display = hasActiveFilters ? "inline-flex" : "none";

  CURRENT_LEADS = scope
    .filter((l) => {
      if (state.tab !== "ALL" && offerOf(l) !== state.tab) return false;
      if (niche && l.niche_slug !== niche) return false;
      if (owner && l.assigned_to !== owner) return false;
      if (hideIgnored && (l.lead_status === "nao_fazer" || l.lead_status === "descartado")) return false;
      if (status) {
        const norm = normStatus(l.lead_status);
        if (status === "novo" && norm !== "novo") return false;
        if (status === "vou_fazer" && norm !== "vou-fazer") return false;
        if (status === "fazendo" && norm !== "fazendo") return false;
        if (status === "nao_fazer" && norm !== "nao-fazer") return false;
        if (status === "fechado" && norm !== "fechado") return false;
        if (!["novo", "vou_fazer", "fazendo", "nao_fazer", "fechado"].includes(status) && l.lead_status !== status) return false;
      }
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
  const startIdx = (state.page - 1) * state.pageSize;
  const endIdx = Math.min(startIdx + state.pageSize, CURRENT_LEADS.length);
  const pageLeads = CURRENT_LEADS.slice(startIdx, endIdx);
  if (!pageLeads.some((l) => l.id === state.selectedId)) {
    state.selectedId = pageLeads[0] ? pageLeads[0].id : null;
  }
  renderDetail();
}

function applyQuickTab(tab) {
  state.tab = tab;
  if (tab === "ALL") {
    state.kpiNoSite = false;
    state.kpiContacted = false;
    ["filter-whatsapp", "filter-domain-free", "filter-hide-ignored"].forEach((id) => {
      const el = $(id);
      if (el) el.checked = false;
    });
    ["filter-niche", "filter-owner", "filter-status", "filter-search"].forEach((id) => {
      const el = $(id);
      if (el) el.value = "";
    });
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
  const siteDown = scope.filter((l) => offerOf(l) === "REFORMA_SITE").length;
  const complex = scope.filter((l) => offerOf(l) === "SISTEMA_COMPLEXO").length;
  const dom = scope.filter((l) => l.domain_available_br).length;
  const offers = { SITE_NOVO: 0, REFORMA_SITE: 0, SISTEMA_COMPLEXO: 0 };
  scope.forEach((l) => offers[offerOf(l)]++);

  const setTxt = (id, val) => {
    const el = $(id);
    if (el) el.textContent = val;
  };

  setTxt("scope-label", scope.length ? `${SCOPE_CITY}, ${scope[0].state || ""}` : "Sem cidade");
  setTxt("exec-summary-headline", total ? `Clientes em ${SCOPE_CITY}` : "Clientes");
  setTxt(
    "exec-summary-subtext",
    total
      ? `${fmtInt(noSite)} de ${fmtInt(total)} empresas não têm site próprio e ${fmtInt(dom)} têm o domínio .com.br livre. Comece pelas de maior chance.`
      : "Escolha os nichos na barra lateral e clique em Buscar clientes reais."
  );
  setTxt("stat-total", fmtInt(total));
  setTxt("stat-without-site", fmtInt(noSite));
  setTxt("stat-site-down", fmtInt(siteDown));
  setTxt("stat-complex", fmtInt(complex));
  setTxt("stat-domain-free", fmtInt(dom));

  const countVou = scope.filter((l) => normStatus(l.lead_status) === "vou-fazer").length;
  const countFazendo = scope.filter((l) => normStatus(l.lead_status) === "fazendo").length;
  const countNao = scope.filter((l) => normStatus(l.lead_status) === "nao-fazer").length;
  const countFechado = scope.filter((l) => normStatus(l.lead_status) === "fechado").length;
  const countNovo = scope.filter((l) => normStatus(l.lead_status) === "novo").length;

  setTxt("count-status-all", fmtInt(total));
  setTxt("count-status-vou", fmtInt(countVou));
  setTxt("count-status-fazendo", fmtInt(countFazendo));
  setTxt("count-status-nao", fmtInt(countNao));
  setTxt("count-status-fechado", fmtInt(countFechado));
  setTxt("count-status-novo", fmtInt(countNovo));

  document.querySelectorAll(".decision-pill-btn").forEach((btn) => {
    btn.classList.toggle("active", (btn.dataset.statusFilter || "") === (state.statusFilter || ""));
  });

  document.querySelectorAll("[data-count]").forEach((el) => {
    const k = el.dataset.count;
    el.textContent = k === "ALL" ? fmtInt(total) : fmtInt(offers[k] || 0);
  });
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === state.tab));

  const filterWpp = $("filter-whatsapp");
  const filterDom = $("filter-domain-free");
  const on = {
    ALL: state.tab === "ALL",
    SITE_NOVO: state.tab === "SITE_NOVO",
    REFORMA_SITE: state.tab === "REFORMA_SITE",
    SISTEMA_COMPLEXO: state.tab === "SISTEMA_COMPLEXO",
    DOMAIN: filterDom ? !!filterDom.checked : false,
  };
  document.querySelectorAll("[data-kpi]").forEach((k) => k.classList.toggle("on", !!on[k.dataset.kpi]));
  const now = new Date();
  setTxt("stamp", total ? `Atualizado ${now.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}` : "");
}

/* ---------- lista ---------- */
function renderSkeleton() {
  const grid = $("ready-reports-grid");
  if (!grid) return;
  grid.innerHTML = Array.from({ length: 6 })
    .map(() => `<div class="skel"><i style="width:${40 + Math.round(Math.random() * 30)}%"></i></div>`)
    .join("");
}

function renderError(msg) {
  const grid = $("ready-reports-grid");
  if (!grid) return;
  grid.innerHTML = `<div class="empty"><strong>Não foi possível carregar as empresas.</strong>${esc(msg)}<br/><button class="btn btn-sm" onclick="loadLeads()">Tentar de novo</button></div>`;
}

function shortAddress(addr) {
  const parts = String(addr || "").split(",").map((s) => s.trim());
  return parts.slice(0, 2).join(", ");
}

function renderRows() {
  const box = $("ready-reports-grid");
  if (!box) return;
  const total = CURRENT_LEADS.length;

  if (!scopeLeads().length) {
    box.innerHTML = `<div class="empty"><strong>Nenhuma empresa ainda.</strong>Marque os nichos na barra lateral e busque uma cidade.<br/><button class="btn btn-primary btn-sm" onclick="document.getElementById('input-city').focus()">Escolher cidade</button></div>`;
    const listTotal = $("list-total");
    if (listTotal) listTotal.textContent = "0 empresas";
    renderPagination(0, 1, 0, 0);
    return;
  }
  if (!total) {
    box.innerHTML = `<div class="empty"><strong>Nenhuma empresa neste filtro.</strong>Tire algum filtro para ver mais.<br/><button class="btn btn-sm" onclick="applyQuickTab('ALL')">Limpar filtros</button></div>`;
    const listTotal = $("list-total");
    if (listTotal) listTotal.textContent = "0 empresas";
    renderPagination(0, 1, 0, 0);
    return;
  }

  const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
  if (state.page > totalPages) state.page = totalPages;
  if (state.page < 1) state.page = 1;

  const startIdx = (state.page - 1) * state.pageSize;
  const endIdx = Math.min(startIdx + state.pageSize, total);

  const listTotal = $("list-total");
  if (listTotal) {
    listTotal.textContent = `Pág. ${state.page} de ${totalPages} · ${fmtInt(total)} empresas`;
  }

  const displayedLeads = state.isPrinting ? CURRENT_LEADS : CURRENT_LEADS.slice(startIdx, endIdx);

  box.innerHTML = displayedLeads
    .map((l) => {
      const offer = offerOf(l);
      const sel = l.id === state.selectedId;
      const rating = fmtRating(l.review_rating);
      const score = l.opportunity_score || 0;
      const stNorm = normStatus(l.lead_status);
      return `
      <div class="row ${sel ? "selected" : ""} status-${stNorm} ${isContacted(l) ? "contacted" : ""}" role="option" aria-selected="${sel}" tabindex="0" data-id="${l.id}"
           onclick="selectLead(${l.id}, {overlay:true})" onkeydown="if(event.key==='Enter'){selectLead(${l.id}, {overlay:true})}">
        <div style="min-width:0">
          <div class="name">${esc(l.title)}</div>
          <div class="sub2">${esc(l.category || "Empresa")} · ${l.review_count ? fmtInt(l.review_count) + " avaliações" : "sem avaliações"}</div>
        </div>
        <div><span class="pill ${PILL_CLASS[offer]}">${SERVICE_LABELS[offer]}</span></div>
        <div class="cell-r num cell-note">${rating ? esc(rating) : '<span class="dash">—</span>'}</div>
        <div class="cell-r num score cell-score ${score >= 85 ? "hi" : ""}">${score}</div>
        <div class="cell-r" onclick="event.stopPropagation()">
          <select class="lead-status-select pill-${stNorm}" aria-label="Decisão para ${esc(l.title)}" onchange="quickUpdateLeadStatus(${l.id}, this.value)">
            <option value="novo" ${stNorm === "novo" ? "selected" : ""}>⚪ Novo</option>
            <option value="vou_fazer" ${stNorm === "vou-fazer" ? "selected" : ""}>🎯 Vou fazer</option>
            <option value="fazendo" ${stNorm === "fazendo" ? "selected" : ""}>⏳ Fazendo</option>
            <option value="nao_fazer" ${stNorm === "nao-fazer" ? "selected" : ""}>❌ Não fazer</option>
            <option value="fechado" ${stNorm === "fechado" ? "selected" : ""}>✅ Fechado</option>
          </select>
        </div>
      </div>`;
    })
    .join("");

  renderPagination(total, totalPages, startIdx, endIdx);
}

function renderPagination(total, totalPages, startIdx, endIdx) {
  const bar = $("pagination-bar");
  if (!bar) return;

  if (total === 0) {
    bar.style.display = "none";
    return;
  }
  bar.style.display = "flex";

  const pageInfo = $("page-info");
  if (pageInfo) {
    pageInfo.textContent = `${fmtInt(startIdx + 1)}–${fmtInt(endIdx)} de ${fmtInt(total)}`;
  }

  const sizeSelect = $("page-size-select");
  if (sizeSelect && Number(sizeSelect.value) !== state.pageSize) {
    sizeSelect.value = String(state.pageSize);
  }

  const btnPrev = $("btn-prev-page");
  if (btnPrev) {
    btnPrev.disabled = state.page <= 1;
  }
  const btnNext = $("btn-next-page");
  if (btnNext) {
    btnNext.disabled = state.page >= totalPages;
  }

  const pagesContainer = $("pagination-pages");
  if (pagesContainer) {
    pagesContainer.innerHTML = buildPaginationButtons(state.page, totalPages);
  }
}

function buildPaginationButtons(current, total) {
  if (total <= 1) return "";

  const pages = [];
  const delta = 1;

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i);
  } else {
    pages.push(1);
    if (current > delta + 2) {
      pages.push("...");
    }
    const start = Math.max(2, current - delta);
    const end = Math.min(total - 1, current + delta);
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    if (current < total - (delta + 1)) {
      pages.push("...");
    }
    pages.push(total);
  }

  return pages
    .map((p) => {
      if (p === "...") {
        return `<span class="pagination-ellipsis">&hellip;</span>`;
      }
      const isActive = p === current;
      return `<button type="button" class="btn-page-num ${isActive ? "active" : ""}" aria-current="${isActive ? "page" : "false"}" onclick="goToPage(${p})">${p}</button>`;
    })
    .join("");
}

function goToPage(p) {
  const total = CURRENT_LEADS.length;
  const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
  const newPage = Math.max(1, Math.min(p, totalPages));
  if (newPage === state.page && !state.isPrinting) return;
  state.page = newPage;
  renderRows();

  const startIdx = (state.page - 1) * state.pageSize;
  const endIdx = Math.min(startIdx + state.pageSize, total);
  const pageLeads = CURRENT_LEADS.slice(startIdx, endIdx);
  if (pageLeads.length && !pageLeads.some((l) => l.id === state.selectedId)) {
    selectLead(pageLeads[0].id, { scroll: false, overlay: false });
  }

  const box = $("ready-reports-grid");
  if (box) box.scrollTop = 0;
}

function onPageSizeChange(newSize) {
  const val = Number(newSize) || 5;
  state.pageSize = val;
  state.limit = val;
  state.page = 1;
  try {
    localStorage.setItem("painel_page_size", String(val));
  } catch (e) {}
  renderRows();

  const startIdx = 0;
  const endIdx = Math.min(state.pageSize, CURRENT_LEADS.length);
  const pageLeads = CURRENT_LEADS.slice(startIdx, endIdx);
  if (pageLeads.length && !pageLeads.some((l) => l.id === state.selectedId)) {
    selectLead(pageLeads[0].id, { scroll: false, overlay: false });
  }
}

function showMoreRows() {
  goToPage(state.page + 1);
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

    ${renderDecisionButtonsHtml(l)}

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
        <button class="btn btn-sm" type="button" onclick="generatePrototypeFromCard(${l.id})">🎨 Gerar / Ver Protótipo IA</button>
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
          <select id="detail-select-status" onchange="quickUpdateLeadStatus(${l.id}, this.value)">
            ${[["novo", "⚪ Novo"], ["vou_fazer", "🎯 Vou fazer"], ["fazendo", "⏳ Estou fazendo"], ["fechado", "✅ Fechado"], ["nao_fazer", "❌ Não vou fazer"], ["analisado", "Analisado"], ["contatado", "Já chamei"], ["respondeu", "Respondeu"], ["reuniao", "Reunião"], ["descartado", "Descartado"]]
              .map(([v, t]) => `<option value="${v}" ${l.lead_status === v ? "selected" : ""}>${t}</option>`)
              .join("")}
          </select></label>
      </div>
    </div>`;
}

function renderDecisionButtonsHtml(l) {
  const stNorm = normStatus(l.lead_status);
  return `
  <div class="d-decision-box">
    <div class="d-label">Minha decisão para este cliente</div>
    <div class="decision-buttons" id="decision-buttons-box">
      <button type="button" class="btn-decision btn-decision-vou ${stNorm === "vou-fazer" ? "active" : ""}" onclick="quickUpdateLeadStatus(${l.id}, 'vou_fazer')">
        🎯 Vou fazer
      </button>
      <button type="button" class="btn-decision btn-decision-fazendo ${stNorm === "fazendo" ? "active" : ""}" onclick="quickUpdateLeadStatus(${l.id}, 'fazendo')">
        ⏳ Estou fazendo
      </button>
      <button type="button" class="btn-decision btn-decision-nao ${stNorm === "nao-fazer" ? "active" : ""}" onclick="quickUpdateLeadStatus(${l.id}, 'nao_fazer')">
        ❌ Não vou fazer
      </button>
      <button type="button" class="btn-decision btn-decision-fechado ${stNorm === "fechado" ? "active" : ""}" onclick="quickUpdateLeadStatus(${l.id}, 'fechado')">
        ✅ Fechado
      </button>
    </div>
    <div class="d-agent-action-bar">
      <button type="button" class="btn btn-agent-enqueue" onclick="enqueueSingleLead(${l.id}, 'whatsapp')">
        🤖 Enviar p/ Fila do Agente &amp; Negociar
      </button>
      <a href="#agente" class="btn btn-sm btn-agent-goto" title="Ver Central do Agente">
        Ver Agente →
      </a>
    </div>
  </div>`;
}

function renderDecisionButtons(currentStatus, leadId) {
  const box = $("decision-buttons-box");
  if (!box) return;
  const stNorm = normStatus(currentStatus);
  box.innerHTML = `
    <button type="button" class="btn-decision btn-decision-vou ${stNorm === "vou-fazer" ? "active" : ""}" onclick="quickUpdateLeadStatus(${leadId}, 'vou_fazer')">
      🎯 Vou fazer
    </button>
    <button type="button" class="btn-decision btn-decision-fazendo ${stNorm === "fazendo" ? "active" : ""}" onclick="quickUpdateLeadStatus(${leadId}, 'fazendo')">
      ⏳ Estou fazendo
    </button>
    <button type="button" class="btn-decision btn-decision-nao ${stNorm === "nao-fazer" ? "active" : ""}" onclick="quickUpdateLeadStatus(${leadId}, 'nao_fazer')">
      ❌ Não vou fazer
    </button>
    <button type="button" class="btn-decision btn-decision-fechado ${stNorm === "fechado" ? "active" : ""}" onclick="quickUpdateLeadStatus(${leadId}, 'fechado')">
      ✅ Fechado
    </button>`;
}

async function quickUpdateLeadStatus(leadId, newStatus) {
  const leadAll = ALL_LEADS.find((x) => x.id === leadId);
  if (leadAll) leadAll.lead_status = newStatus;
  const leadCur = CURRENT_LEADS.find((x) => x.id === leadId);
  if (leadCur) leadCur.lead_status = newStatus;

  const stNorm = normStatus(newStatus);
  const rowEl = document.querySelector(`.row[data-id="${leadId}"]`);
  if (rowEl) {
    rowEl.className = `row ${leadId === state.selectedId ? "selected" : ""} status-${stNorm} ${isContacted(leadCur || leadAll || {}) ? "contacted" : ""}`;
    const sel = rowEl.querySelector(".lead-status-select");
    if (sel) {
      sel.value = newStatus;
      sel.className = `lead-status-select pill-${stNorm}`;
    }
  }

  if (state.selectedId === leadId) {
    renderDecisionButtons(newStatus, leadId);
    const detailSel = $("detail-select-status");
    if (detailSel) detailSel.value = newStatus;
  }

  const hideIgnored = $("filter-hide-ignored") && $("filter-hide-ignored").checked;
  const filterStatusVal = $("filter-status") && $("filter-status").value;
  if ((hideIgnored && stNorm === "nao-fazer") || (filterStatusVal && filterStatusVal !== newStatus)) {
    applyFilters();
  } else {
    renderSummary(scopeLeads());
  }

  try {
    await fetch(`/api/leads/${leadId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lead_status: newStatus }),
    });
  } catch (err) {
    console.error("Falha ao atualizar status do lead:", err);
  }
}

async function updateLeadOwnerOrStatus(leadId, patch) {
  if (patch.lead_status) {
    await quickUpdateLeadStatus(leadId, patch.lead_status);
  }
  if (patch.assigned_to) {
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
}

async function markLeadContacted(leadId) {
  const l = ALL_LEADS.find((x) => x.id === leadId);
  if (l && (l.lead_status === "novo" || l.lead_status === "analisado")) {
    await updateLeadOwnerOrStatus(leadId, { lead_status: "contatado" });
    renderDetail();
  }
}

/* ---------- WhatsApp & Ações de Contato ---------- */
function cleanWhatsAppNumber(raw) {
  if (!raw) return "";
  let digits = String(raw).replace(/\D/g, "");
  if (!digits) return "";
  if (digits.startsWith("0")) digits = digits.substring(1);
  if (digits.length === 10 || digits.length === 11) {
    digits = "55" + digits;
  }
  return digits;
}

function openWhatsApp(leadId, customMsg) {
  const l = ALL_LEADS.find((x) => x.id === leadId) || CURRENT_LEADS.find((x) => x.id === leadId);
  if (!l) return;

  const rawNum = waNumber(l) || l.phone || "";
  const phone = cleanWhatsAppNumber(rawNum);
  if (!phone) {
    alert("Esta empresa não possui um telefone ou WhatsApp cadastrado com DDD.");
    return;
  }

  let text = customMsg;
  if (text == null) {
    const cardTextarea = $(`card-wpp-${leadId}`);
    if (cardTextarea && cardTextarea.value.trim()) {
      text = cardTextarea.value.trim();
    } else {
      text = ((l.outreach_scripts || {}).whatsapp || "").trim();
    }
  }

  const encoded = encodeURIComponent(text || "");
  const url = `https://api.whatsapp.com/send?phone=${phone}${encoded ? `&text=${encoded}` : ""}`;

  const fb = $(`copied-${leadId}`);
  if (fb) {
    fb.textContent = "Abrindo WhatsApp...";
    setTimeout(() => {
      if (fb.textContent === "Abrindo WhatsApp...") fb.textContent = "";
    }, 2500);
  }

  // Abertura com fallback anti-bloqueador de pop-ups (window.open + click em âncora)
  try {
    const win = window.open(url, "_blank", "noopener,noreferrer");
    if (!win || win.closed || typeof win.closed === "undefined") {
      const a = document.createElement("a");
      a.href = url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      document.body.appendChild(a);
      a.click();
      setTimeout(() => a.remove(), 300);
    }
  } catch (err) {
    const a = document.createElement("a");
    a.href = url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => a.remove(), 300);
  }

  markLeadContacted(leadId).catch((err) => console.error("Falha ao marcar lead como contatado:", err));
}

function copyCardMessage(leadId) {
  const cardTextarea = $(`card-wpp-${leadId}`);
  const text = cardTextarea ? cardTextarea.value : "";
  if (!text) return;

  const setFeedback = (msg) => {
    const fb = $(`copied-${leadId}`);
    if (fb) {
      fb.textContent = msg;
      setTimeout(() => {
        if (fb.textContent === msg) fb.textContent = "";
      }, 2500);
    }
  };

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text)
      .then(() => setFeedback("Mensagem copiada!"))
      .catch(() => {
        try {
          cardTextarea.select();
          document.execCommand("copy");
          setFeedback("Mensagem copiada!");
        } catch (e) {
          setFeedback("Falha ao copiar");
        }
      });
  } else {
    try {
      cardTextarea.select();
      document.execCommand("copy");
      setFeedback("Mensagem copiada!");
    } catch (e) {
      setFeedback("Falha ao copiar");
    }
  }
}

// Vinculação explícita ao escopo global (window) para eventos inline onclick
window.openWhatsApp = openWhatsApp;
window.copyCardMessage = copyCardMessage;
window.cleanWhatsAppNumber = cleanWhatsAppNumber;
window.markLeadContacted = markLeadContacted;

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
  const body = $("queue-modal-body");
  if (body) body.innerHTML = `<div class="empty">Carregando fila, configurações do Agente e conversas…</div>`;
  $("queue-modal").classList.add("open");
  await refreshAgentViews();
}

async function renderAgentDashboardView() {
  const container = $("view-agente-body");
  if (!container) return;
  container.innerHTML = `<div class="empty">Carregando Central do Agente WhatsApp, Fila e Protótipos IA…</div>`;
  const html = await buildAgentFullDashboardHtml();
  container.innerHTML = html;
}

async function renderQueueModalContent() {
  await refreshAgentViews();
}

async function refreshAgentViews() {
  const html = await buildAgentFullDashboardHtml();
  if ($("view-agente-body")) $("view-agente-body").innerHTML = html;
  if ($("queue-modal-body")) $("queue-modal-body").innerHTML = html;
  await loadHealthAndStats();
}

async function buildAgentFullDashboardHtml() {
  const [settingsBundle, items, convs, consultations] = await Promise.all([
    fetch("/api/agent/settings").then((r) => r.json()).catch(() => ({})),
    fetch("/api/outreach/queue").then((r) => r.json()).catch(() => []),
    fetch("/api/agent/conversations").then((r) => r.json()).catch(() => []),
    fetch("/api/agent/price-consultations").then((r) => r.json()).catch(() => []),
  ]);

  const st = settingsBundle.settings || {
    test_mode: true,
    boss_phone: "551999958516",
    test_client_phone: "5519996109028",
  };
  const ai = settingsBundle.ai_status || {};
  const bridge = settingsBundle.bridge || {};
  const readyCount = (items || []).filter((i) => i.status === "ready").length;

  const qrBlock = bridge.qr_data_url
    ? `<div class="agent-qr-box">
         <div><strong>Escaneie o QR Code com o WhatsApp do Agente:</strong></div>
         <img src="${esc(bridge.qr_data_url)}" alt="QR Code WhatsApp" style="width:170px;height:170px;border-radius:8px;margin-top:6px;background:#fff;padding:6px;" />
       </div>`
    : `<div class="meta">Bridge WhatsApp: <strong>${bridge.connected ? "🟢 Conectado (" + esc(bridge.phone || "Online") + ")" : "⚪ Aguardando conexão QR (`cd whatsapp_bridge && npm start`)"}</strong> · IA (chave.env): <strong>${esc((ai.active_providers || ["Pronto"]).join(", "))}</strong></div>`;

  const queueRowsHtml = (items || []).length
    ? `<table class="table-leads">
        <thead>
          <tr>
            <th>Empresa</th>
            <th>Destino Efetivo</th>
            <th>Situação</th>
            <th>1ª Mensagem</th>
            <th>Ação</th>
          </tr>
        </thead>
        <tbody>${items
          .map((it) => {
            const destLabel = st.test_mode
              ? `🧪 Teste: ${esc(st.test_client_phone)} (Lead: ${esc(it.recipient)})`
              : `🚀 Real: ${esc(it.recipient)}`;
            const canSend = it.status === "ready" || it.status === "failed";
            return `<tr>
              <td><strong>${esc(it.lead_title || "Empresa #" + it.lead_id)}</strong><br/><span class="meta">${esc(it.lead_city || "")}</span></td>
              <td>${esc(it.channel)}<br/><span class="meta">${destLabel}</span></td>
              <td><span class="pain-tag">${esc(it.status)}</span></td>
              <td style="white-space:pre-wrap;max-width:340px;font-size:12px">${esc(it.message_body)}</td>
              <td>
                <button class="btn btn-sm ${canSend ? "btn-primary" : ""}" type="button" onclick="confirmAndSendQueueItem(${it.id})">
                  ${it.status === "sent" ? "Reenviar 1ª Msg" : "✅ Confirmar e Iniciar"}
                </button>
              </td>
            </tr>`;
          })
          .join("")}</tbody>
      </table>`
    : `<div class="empty"><strong>A fila está vazia.</strong>Use o botão “🤖 Enviar p/ Fila do Agente” no detalhe de uma empresa para colocá-la na fila.</div>`;

  const convRowsHtml = (convs || []).length
    ? `<div class="agent-conv-list">
        ${convs
          .map((c) => {
            const isPaused = c.status === "paused_by_human";
            return `<div class="agent-conv-card">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
                <div>
                  <strong>#${c.id} · ${esc(c.lead_title || "Lead #" + c.lead_id)}</strong>
                  <span class="meta">(${esc(c.chatid)} · ${c.is_test_session ? "🧪 Sessão de Teste" : "🚀 Cliente Real"})</span>
                </div>
                <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
                  <span class="pain-tag">${esc(c.status)}</span>
                  ${
                    c.approved_price_text
                      ? `<span class="embedded-pill ok">Preço aprovado: ${esc(c.approved_price_text)}</span>`
                      : ""
                  }
                  ${
                    isPaused
                      ? `<button class="btn btn-sm" type="button" onclick="toggleConversationPause(${c.id}, false)">▶️ Retomar Agente</button>`
                      : `<button class="btn btn-sm" type="button" onclick="toggleConversationPause(${c.id}, true)">⏸️ Assumir / Pausar</button>`
                  }
                  <button class="btn btn-sm" type="button" onclick="generatePrototypeFromCard(${c.lead_id})">🎨 Protótipo IA</button>
                  ${
                    c.has_prototype
                      ? `<a class="btn btn-sm btn-primary" href="/api/agent/prototypes/${c.lead_id}/preview" target="_blank">Abrir Preview</a>`
                      : ""
                  }
                </div>
              </div>
              <div class="agent-sim-row" style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">
                <input id="sim-client-msg-${c.id}" type="text" placeholder="Simular resposta do cliente (ex: Quanto custa uma LP? / Fechado, pode montar)..." style="flex:1;min-width:220px;" />
                <button class="btn btn-sm" type="button" onclick="simulateWebhookMessage('${esc(c.chatid)}', 'sim-client-msg-${c.id}')">Enviar como Cliente</button>
              </div>
            </div>`;
          })
          .join("")}
      </div>`
    : `<div class="meta" style="padding:8px 0">Nenhuma conversa ativa ainda. Confirme um item na fila acima para disparar a 1ª mensagem e iniciar a negociação!</div>`;

  const pendingConsultsHtml = (consultations || []).length
    ? `<div style="margin-top:12px">
        <div class="d-label">Consultas de Preço enviadas para seu WhatsApp (+${esc(st.boss_phone)})</div>
        ${consultations
          .slice(0, 5)
          .map(
            (p) => `<div class="agent-conv-card" style="margin-top:6px">
              <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;">
                <div><strong>Consulta #${p.id} · ${esc(p.lead_title || "Lead #" + p.lead_id)}</strong> — Pedido: <em>"${esc(p.client_summary)}"</em></div>
                <span class="pain-tag">${esc(p.status)}</span>
              </div>
              <div class="meta" style="margin-top:4px">Faixa: ${esc(p.price_range_text)} · Sugestão do Agente: <strong>R$ ${Math.round((p.suggested_price_cents || 0) / 100)}</strong> ${p.boss_reply_text ? "· Aprovado: <strong>" + esc(p.boss_reply_text) + "</strong>" : ""}</div>
              <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;">
                <input id="boss-reply-${p.id}" type="text" placeholder="Responder preço como Chefe (ex: R$ 1.350 em 3x)..." style="flex:1;min-width:200px;" />
                <button class="btn btn-sm btn-primary" type="button" onclick="approvePriceFromModal(${p.id})">Aprovar e Enviar Proposta ao Cliente</button>
              </div>
            </div>`
          )
          .join("")}
      </div>`
    : "";

  return `
    <div class="agent-control-box" style="padding:12px;border:1px solid var(--border);border-radius:10px;margin-bottom:14px;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:10px;">
        <div>
          <strong>Modo Atual de Disparo:</strong>
          <span class="embedded-pill ${st.test_mode ? "warn" : "ok"}" style="margin-left:6px">
            ${st.test_mode ? "🧪 MODO TESTE (Envia só para +" + esc(st.test_client_phone) + ")" : "🚀 MODO PRODUÇÃO (Envia para o WhatsApp real dos clientes)"}
          </span>
        </div>
        <button class="btn btn-sm ${st.test_mode ? "btn-primary" : ""}" type="button" onclick="toggleAgentTestMode(${!st.test_mode})">
          ${st.test_mode ? "✅ Aprovar e Virar para Produção (Clientes Reais)" : "Voltar para Modo Teste"}
        </button>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;align-items:end;margin-bottom:8px;">
        <label class="field"><span>Seu WhatsApp Chefe (Preços/Avisos)</span>
          <input id="cfg-boss-phone" type="text" value="${esc(st.boss_phone || "551999958516")}" />
        </label>
        <label class="field"><span>WhatsApp Cliente de Teste (2º Número)</span>
          <input id="cfg-test-phone" type="text" value="${esc(st.test_client_phone || "5519996109028")}" />
        </label>
        <button class="btn btn-sm" type="button" onclick="saveAgentPhonesConfig()">Salvar Números</button>
      </div>
      ${qrBlock}
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
      <div class="d-label" style="margin:0">1. Fila de Aprovação (${items.length} na fila · ${readyCount} prontos)</div>
      ${
        readyCount > 0
          ? `<button class="btn btn-sm btn-primary" type="button" onclick="confirmAndSendAllReady()">🚀 Confirmar e Disparar Todos Prontos (${readyCount})</button>`
          : ""
      }
    </div>
    ${queueRowsHtml}

    <div style="margin-top:18px">
      <div class="d-label">2. Conversas em Negociação &amp; Handoff Humano (90%)</div>
      ${convRowsHtml}
      ${pendingConsultsHtml}
    </div>
  `;
}

async function toggleAgentTestMode(newTestMode) {
  await fetch("/api/agent/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ test_mode: Boolean(newTestMode) }),
  });
  await refreshAgentViews();
}

async function saveAgentPhonesConfig() {
  const bossPhone = ($("cfg-boss-phone") && $("cfg-boss-phone").value) || "551999958516";
  const testPhone = ($("cfg-test-phone") && $("cfg-test-phone").value) || "5519996109028";
  await fetch("/api/agent/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ boss_phone: bossPhone, test_client_phone: testPhone }),
  });
  await refreshAgentViews();
}

async function confirmAndSendQueueItem(queueId) {
  const res = await fetch(`/api/outreach/${queueId}/confirm-send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    alert(data.detail || "Erro ao confirmar disparo.");
    return;
  }
  await refreshAgentViews();
}

async function confirmAndSendAllReady() {
  await fetch("/api/outreach/confirm-send-all", { method: "POST" });
  await refreshAgentViews();
}

async function toggleConversationPause(convId, shouldPause) {
  const endpoint = shouldPause ? "pause" : "resume";
  await fetch(`/api/agent/conversations/${convId}/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: "intervencao_manual_painel" }),
  });
  await refreshAgentViews();
}

async function simulateWebhookMessage(chatid, inputId) {
  const el = $(inputId);
  const text = (el && el.value || "").trim();
  if (!text) return;
  await fetch("/api/agent/webhook?immediate=true", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      EventType: "messages",
      message: {
        fromMe: false,
        isGroup: false,
        type: "text",
        chatid: chatid,
        text: text,
      },
    }),
  });
  if (el) el.value = "";
  await refreshAgentViews();
}

async function approvePriceFromModal(consultationId) {
  const el = $(`boss-reply-${consultationId}`);
  const replyText = (el && el.value || "").trim() || "R$ 1.390 em até 3x";
  await fetch(`/api/agent/price-consultations/${consultationId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reply_text: replyText }),
  });
  await refreshAgentViews();
}

async function generatePrototypeFromCard(leadId) {
  const fb = $(`copied-${leadId}`);
  if (fb) fb.textContent = "Gerando protótipo IA…";
  const res = await fetch(`/api/agent/leads/${leadId}/generate-prototype`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  const data = await res.json().catch(() => ({}));
  if (fb) setTimeout(() => (fb.textContent = ""), 3000);
  if (data && data.prototype && data.prototype.preview_url) {
    window.open(data.prototype.preview_url, "_blank", "noopener,noreferrer");
  }
  await refreshAgentViews();
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
  const numModal = cleanWhatsAppNumber(waNumber(l) || l.phone || "");

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
          <div style="display:flex;justify-content:space-between;margin-bottom:6px">
            <strong>WhatsApp</strong>
            <span style="display:flex;gap:6px">
              <button class="btn btn-sm" type="button" onclick="copyText('modal-wpp-text')">Copiar</button>
              ${numModal ? `<button class="btn btn-sm btn-primary" type="button" onclick="openWhatsApp(${l.id}, $('modal-wpp-text') ? $('modal-wpp-text').value : null)">Chamar no WhatsApp</button>` : ""}
            </span>
          </div>
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

window.confirmAndSendQueueItem = confirmAndSendQueueItem;
window.confirmAndSendAllReady = confirmAndSendAllReady;
window.toggleAgentTestMode = toggleAgentTestMode;
window.saveAgentPhonesConfig = saveAgentPhonesConfig;
window.toggleConversationPause = toggleConversationPause;
window.simulateWebhookMessage = simulateWebhookMessage;
window.approvePriceFromModal = approvePriceFromModal;
window.generatePrototypeFromCard = generatePrototypeFromCard;
window.renderAgentDashboardView = renderAgentDashboardView;
window.refreshAgentViews = refreshAgentViews;

window.addEventListener("DOMContentLoaded", initDashboard);
