/* Painel de Busca — Análise de leads (ranking de chance de fechar, nichos, preços e plano de disparo).
   Fonte: GET /api/leads/ranking (somente leitura). Gráficos em SVG/CSS puros, sem bibliotecas externas.
   Depende dos helpers globais de app.js: $, esc, fmtInt. */

const AN = {
  data: null,
  loading: false,
  error: "",
  filters: { segment: "", tier: "", ready: false, q: "" },
  sort: { key: "rank", dir: 1 },
  shown: 20,
  openId: null,
  startDate: "",
  conv: (() => {
    try {
      const saved = JSON.parse(localStorage.getItem("painel_an_conv") || "null");
      if (saved && ["A", "B", "C", "D"].every((t) => typeof saved[t] === "number")) return saved;
    } catch (e) {}
    return { A: 15, B: 8, C: 4, D: 2 };
  })(),
};

const AN_TIERS = ["A", "B", "C", "D"];
const AN_CHANNEL = { whatsapp: "WhatsApp (celular)", telefone: "Telefone fixo", instagram: "Só Instagram", email: "Só e-mail", nenhum: "Sem contato" };
const AN_FLAG = {
  TELEFONE_DUPLICADO: "Telefone repetido",
  JA_NA_FILA: "Já na fila",
  EM_ANDAMENTO: "Em andamento",
  SEM_WHATSAPP_DIRETO: "Sem WhatsApp direto",
  DESCARTADO_MANUALMENTE: "Descartado",
  INSTITUICAO_PUBLICA_OU_ENSINO: "Instituição pública/ensino",
  LEAD_SIMULADO: "Lead simulado",
};

const anBRL = (cents) => "R$ " + Math.round((cents || 0) / 100).toLocaleString("pt-BR");
function anBRLShort(cents) {
  const v = (cents || 0) / 100;
  if (v >= 1000000) return "R$ " + (v / 1000000).toFixed(1).replace(".", ",") + " mi";
  if (v >= 10000) return "R$ " + Math.round(v / 1000).toLocaleString("pt-BR") + " mil";
  if (v >= 1000) return "R$ " + (v / 1000).toFixed(1).replace(".", ",") + " mil";
  return "R$ " + Math.round(v);
}
const anPct = (n, d) => (d ? Math.round((n / d) * 100) : 0);

/* ---------- carga ---------- */
async function loadAnalysis(force) {
  if (AN.loading || (AN.data && !force)) return;
  AN.loading = true;
  AN.error = "";
  renderAnalysisView();
  try {
    const res = await fetch("/api/leads/ranking?per_day=20");
    if (res.status === 422) {
      throw new Error("servidor antigo na porta 8090 — reinicie o Painel (iniciar_painel.bat) para carregar a rota /api/leads/ranking");
    }
    if (!res.ok) throw new Error("HTTP " + res.status);
    AN.data = await res.json();
  } catch (e) {
    AN.error = "Não foi possível carregar o ranking (" + e.message + ").";
  }
  AN.loading = false;
  renderAnalysisView();
}

function anNextBusinessDay(from) {
  const d = new Date(from.getTime());
  d.setDate(d.getDate() + 1);
  while (d.getDay() === 0 || d.getDay() === 6) d.setDate(d.getDate() + 1);
  return d;
}

function anPlanLabel(index) {
  // Dia N considerando só dias úteis a partir da data inicial
  let d = AN.startDate ? new Date(AN.startDate + "T12:00:00") : anNextBusinessDay(new Date());
  let n = 0;
  while (n < index) {
    d = anNextBusinessDay(d);
    n += 1;
  }
  const wd = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"][d.getDay()];
  return wd + " " + String(d.getDate()).padStart(2, "0") + "/" + String(d.getMonth() + 1).padStart(2, "0");
}

/* ---------- gráficos ---------- */
function anFunnel(funnel) {
  const top = funnel[0].count || 1;
  return (
    '<div class="an-funnel">' +
    funnel
      .map((s, i) => {
        const prev = i ? funnel[i - 1].count : s.count;
        const drop = i && prev ? "−" + (100 - anPct(s.count, prev)) + "% vs. etapa anterior" : "base de partida";
        return (
          '<div class="an-frow" title="' + esc(s.label + ": " + s.count) + '">' +
          '<div class="an-flabel">' + esc(s.label) + "</div>" +
          '<div class="an-ftrack"><div class="an-fbar" style="width:' + Math.max(2, anPct(s.count, top)) + '%"></div></div>' +
          '<div class="an-fval num">' + fmtInt(s.count) + '<span class="an-fdrop">' + esc(drop) + "</span></div></div>"
        );
      })
      .join("") +
    "</div>"
  );
}

function anHistogram(bins) {
  const W = 520, H = 220, L = 34, B = 28, T = 10, R = 8;
  const max = Math.max(1, ...bins.map((b) => b.count));
  const niceMax = Math.ceil(max / 5) * 5 || 5;
  const bw = (W - L - R) / bins.length;
  let g = "";
  for (let i = 0; i <= 4; i++) {
    const v = (niceMax / 4) * i;
    const y = H - B - ((H - B - T) * v) / niceMax;
    g += '<line class="an-grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + y + '" y2="' + y + '"/><text class="an-axis" x="' + (L - 6) + '" y="' + (y + 4) + '" text-anchor="end">' + Math.round(v) + "</text>";
  }
  bins.forEach((b, i) => {
    let yCursor = H - B;
    AN_TIERS.slice().reverse().forEach((t) => {
      const c = b.tiers[t] || 0;
      if (!c) return;
      const h = ((H - B - T) * c) / niceMax;
      yCursor -= h;
      g += '<rect class="an-t t-' + t + '" x="' + (L + i * bw + 3) + '" y="' + yCursor + '" width="' + (bw - 6) + '" height="' + h + '"><title>' + esc("Nota " + b.from + "–" + b.to + " · tier " + t + ": " + c + " lead(s)") + "</title></rect>";
    });
    g += '<text class="an-axis" x="' + (L + i * bw + bw / 2) + '" y="' + (H - 10) + '" text-anchor="middle">' + b.from + "</text>";
  });
  return '<svg class="an-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Distribuição das notas por tier">' + g + "</svg>" + anLegend();
}

function anLegend() {
  const names = { A: "A · Disparar primeiro", B: "B · Segunda leva", C: "C · Terceira leva", D: "D · Baixa prioridade" };
  return '<div class="an-legend">' + AN_TIERS.map((t) => '<span class="an-leg t-' + t + '"><i></i>' + names[t] + "</span>").join("") + "</div>";
}

function anScatter(items) {
  const W = 520, H = 300, L = 38, B = 34, T = 10, R = 12;
  const xMax = Math.log10(1000);
  const X = (r) => L + (Math.min(Math.log10((r || 0) + 1), xMax) / xMax) * (W - L - R);
  const Y = (s) => H - B - ((H - B - T) * s) / 100;
  let g = "";
  [0, 20, 40, 60, 80, 100].forEach((v) => {
    g += '<line class="an-grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(v) + '" y2="' + Y(v) + '"/><text class="an-axis" x="' + (L - 6) + '" y="' + (Y(v) + 4) + '" text-anchor="end">' + v + "</text>";
  });
  [[0, "0"], [10, "10"], [100, "100"], [1000, "1000+"]].forEach(([v, label]) => {
    const x = X(v);
    g += '<line class="an-grid" x1="' + x + '" x2="' + x + '" y1="' + T + '" y2="' + (H - B) + '"/><text class="an-axis" x="' + x + '" y="' + (H - 16) + '" text-anchor="middle">' + label + "</text>";
  });
  AN.data.analytics.methodology.tiers.forEach((t) => {
    if (t.min_score > 0) g += '<line class="an-cut" x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(t.min_score) + '" y2="' + Y(t.min_score) + '"/><text class="an-axis an-cut-l" x="' + (W - R - 2) + '" y="' + (Y(t.min_score) - 3) + '" text-anchor="end">tier ' + t.tier + " ≥ " + t.min_score + "</text>";
  });
  items.forEach((it) => {
    if (it.tier === "EXCLUIDO") return;
    g += '<circle class="an-dot t-' + it.tier + '" data-id="' + it.lead_id + '" cx="' + X(it.review_count).toFixed(1) + '" cy="' + Y(it.score).toFixed(1) + '" r="4.2"><title>' +
      esc(it.title + " · nota " + it.score + " · " + it.review_count + " avaliações · " + anBRL(it.price.alvo_cents)) + "</title></circle>";
  });
  g += '<text class="an-axis" x="' + (L + (W - L - R) / 2) + '" y="' + (H - 2) + '" text-anchor="middle">avaliações no Google (escala log)</text>';
  return '<svg class="an-svg an-scatter" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Avaliações versus nota">' + g + "</svg>" + anLegend();
}

function anSegments(segs) {
  const maxCount = Math.max(1, ...segs.map((s) => s.total));
  const maxPrice = Math.max(1, ...segs.map((s) => s.max_price_cents));
  return (
    '<div class="an-seg-head"><span>Nicho</span><span>Leads (prontos / total)</span><span class="r">Nota</span><span class="r">Tier A</span><span>Preço sugerido (mín · média · máx)</span></div>' +
    segs
      .map((s) => {
        const left = anPct(s.min_price_cents, maxPrice), width = Math.max(2, anPct(s.max_price_cents - s.min_price_cents, maxPrice)), avg = anPct(s.avg_price_cents, maxPrice);
        const sel = AN.filters.segment === s.slug ? " on" : "";
        return (
          '<button type="button" class="an-seg' + sel + '" data-slug="' + esc(s.slug) + '" onclick="anPickSegment(\'' + esc(s.slug) + '\')" title="Filtrar tabela por este nicho">' +
          '<span class="an-seg-name">' + esc(s.label) + "</span>" +
          '<span class="an-seg-bar"><span class="an-seg-total" style="width:' + anPct(s.total, maxCount) + '%"><span class="an-seg-ready" style="width:' + anPct(s.ready, s.total) + '%"></span></span><b class="num">' + s.ready + " / " + s.total + "</b></span>" +
          '<span class="r num">' + s.avg_score + "</span>" +
          '<span class="r num">' + s.tier_a + "</span>" +
          '<span class="an-range"><span class="an-range-fill" style="left:' + left + "%;width:" + width + '%"></span><span class="an-range-avg" style="left:' + avg + '%"></span></span>' +
          "</button>" +
          '<div class="an-seg-price num">' + anBRL(s.min_price_cents) + " · <b>" + anBRL(s.avg_price_cents) + "</b> · " + anBRL(s.max_price_cents) + " — carteira pronta: " + anBRLShort(s.ready_value_cents) + "</div>"
        );
      })
      .join("")
  );
}

function anBars(rows, valueKey, labelKey, suffix) {
  const max = Math.max(1, ...rows.map((r) => r[valueKey]));
  return (
    '<div class="an-bars">' +
    rows
      .map(
        (r) =>
          '<div class="an-brow"><span class="an-blabel">' + esc(r[labelKey]) + '</span><span class="an-btrack"><span class="an-bfill" style="width:' + anPct(r[valueKey], max) + '%"></span></span><span class="an-bval num">' + fmtInt(r[valueKey]) + (suffix ? esc(suffix(r)) : "") + "</span></div>"
      )
      .join("") +
    "</div>"
  );
}

function anPlan(days) {
  if (!days.length) return '<div class="empty"><strong>Nenhum lead pronto</strong>Não há leads com celular válido para disparo.</div>';
  const W = 520, H = 230, L = 30, B = 40, T = 10, R = 8;
  const max = Math.max(...days.map((d) => d.count), 1);
  const bw = (W - L - R) / days.length;
  let g = "";
  [0, 0.5, 1].forEach((f) => {
    const y = H - B - (H - B - T) * f;
    g += '<line class="an-grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + y + '" y2="' + y + '"/><text class="an-axis" x="' + (L - 6) + '" y="' + (y + 4) + '" text-anchor="end">' + Math.round(max * f) + "</text>";
  });
  days.forEach((d, i) => {
    let yCursor = H - B;
    const gap = Math.min(12, Math.max(2, bw * 0.2));
    const rectW = Math.max(2, bw - gap);
    AN_TIERS.slice().reverse().forEach((t) => {
      const c = d.tiers[t] || 0;
      if (!c) return;
      const h = ((H - B - T) * c) / max;
      yCursor -= h;
      g += '<rect class="an-t t-' + t + '" x="' + (L + i * bw + gap / 2) + '" y="' + yCursor + '" width="' + rectW + '" height="' + h + '"><title>' + esc("Dia " + d.day + " · tier " + t + ": " + c + " · soma dia: " + anBRLShort(d.value_cents)) + "</title></rect>";
    });
    const cx = L + i * bw + bw / 2;
    g += '<text class="an-axis" x="' + cx + '" y="' + (H - 24) + '" text-anchor="middle">' + esc(anPlanLabel(i)) + '</text><text class="an-axis an-strong" x="' + cx + '" y="' + (H - 10) + '" text-anchor="middle">' + d.count + "</text>";
  });
  return '<svg class="an-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Plano de disparo por dia">' + g + "</svg>" + anLegend();
}

function anSimulator() {
  const bt = AN.data.analytics.pipeline.by_tier;
  let totalClose = 0, totalRev = 0;
  const rows = AN_TIERS.map((t) => {
    const pct = Number(AN.conv[t]) || 0;
    const closes = (bt[t].count * pct) / 100, rev = (bt[t].value_cents * pct) / 100;
    totalClose += closes;
    totalRev += rev;
    return (
      "<tr><td><span class=\"an-leg t-" + t + '"><i></i>Tier ' + t + '</span></td><td class="r num">' + bt[t].count + '</td><td class="r num">' + anBRLShort(bt[t].value_cents) +
      '</td><td class="r"><input class="an-pct num" type="number" min="0" max="100" step="1" value="' + pct + '" oninput="anSetConv(\'' + t + '\', this.value)" aria-label="Taxa de fechamento do tier ' + t + '"> %</td>' +
      '<td class="r num" id="an-sim-c-' + t + '">' + closes.toFixed(1).replace(".", ",") + '</td><td class="r num" id="an-sim-r-' + t + '">' + anBRLShort(rev) + "</td></tr>"
    );
  }).join("");
  return (
    '<div class="an-tablewrap"><table class="an-table"><thead><tr><th>Tier</th><th class="r">Prontos</th><th class="r">Valor na mesa</th><th class="r">Taxa de fechamento (sua premissa)</th><th class="r">Fechamentos</th><th class="r">Receita esperada</th></tr></thead><tbody>' + rows +
    '</tbody><tfoot><tr><td colspan="4"><b>Total esperado</b></td><td class="r num" id="an-sim-ct"><b>' + totalClose.toFixed(1).replace(".", ",") + '</b></td><td class="r num" id="an-sim-rt"><b>' + anBRLShort(totalRev) + "</b></td></tr></tfoot></table></div>" +
    '<p class="meta an-note">As taxas acima são <b>chutes editáveis</b>, não dados medidos. Depois dos primeiros disparos, troque pelos números reais de resposta e fechamento.</p>'
  );
}

function anSetConv(tier, value) {
  AN.conv[tier] = Math.max(0, Math.min(100, Number(value) || 0));
  try { localStorage.setItem("painel_an_conv", JSON.stringify(AN.conv)); } catch (e) {}
  const bt = AN.data.analytics.pipeline.by_tier;
  let c = 0, r = 0;
  AN_TIERS.forEach((t) => {
    const pct = AN.conv[t];
    const cl = (bt[t].count * pct) / 100, rv = (bt[t].value_cents * pct) / 100;
    c += cl;
    r += rv;
    if ($("an-sim-c-" + t)) $("an-sim-c-" + t).textContent = cl.toFixed(1).replace(".", ",");
    if ($("an-sim-r-" + t)) $("an-sim-r-" + t).textContent = anBRLShort(rv);
  });
  if ($("an-sim-ct")) $("an-sim-ct").innerHTML = "<b>" + c.toFixed(1).replace(".", ",") + "</b>";
  if ($("an-sim-rt")) $("an-sim-rt").innerHTML = "<b>" + anBRLShort(r) + "</b>";
}

function anMethodology(m) {
  return (
    '<div class="an-method">' +
    '<div><h4>Como a nota (0–100) é calculada</h4>' +
    m.components
      .map(
        (c) =>
          '<div class="an-mrow"><div class="an-mhead"><b>' + esc(c.label) + '</b><span class="num">até ' + c.max_points + ' pts</span></div><div class="an-btrack"><span class="an-bfill" style="width:' + c.max_points + '%"></span></div><p class="meta">' + esc(c.description) + "</p></div>"
      )
      .join("") +
    "</div><div><h4>Faixas (tiers)</h4>" +
    m.tiers.map((t) => '<div class="an-mtier"><span class="an-leg t-' + t.tier + '"><i></i>Tier ' + t.tier + '</span><span class="num">' + (t.min_score ? "nota ≥ " + t.min_score : "abaixo disso") + "</span><span class=\"meta\">" + esc(t.label) + "</span></div>").join("") +
    "<h4>Preço sugerido</h4><p class=\"meta\">" + esc(m.price) + "</p><h4>Ficam de fora</h4><ul class=\"meta\">" + m.exclusions.map((e) => "<li>" + esc(e) + "</li>").join("") + "</ul><p class=\"meta\"><b>" + esc(m.disclaimer) + "</b></p></div></div>"
  );
}

/* ---------- tabela ---------- */
function anFiltered() {
  const f = AN.filters;
  const q = f.q.trim().toLowerCase();
  let rows = AN.data.ranking.filter(
    (r) =>
      (!f.segment || r.segment.slug === f.segment) &&
      (!f.tier || r.tier === f.tier) &&
      (!f.ready || r.outreach_ready) &&
      (!q || (r.title || "").toLowerCase().includes(q) || (r.whatsapp || "").includes(q))
  );
  const key = AN.sort.key, dir = AN.sort.dir;
  const val = (r) => (key === "price" ? r.price.alvo_cents : key === "reviews" ? r.review_count : key === "score" ? r.score : r.rank);
  rows = rows.slice().sort((a, b) => (val(a) - val(b)) * dir || a.rank - b.rank);
  return rows;
}

function anRow(r) {
  const open = AN.openId === r.lead_id;
  const flags = r.flags.map((f) => '<span class="pill bad">' + esc(AN_FLAG[f] || f) + "</span>").join(" ");
  let html =
    '<tr class="an-tr' + (open ? " open" : "") + '" data-row="' + r.lead_id + '" onclick="anToggleRow(' + r.lead_id + ')">' +
    '<td class="num r">' + r.rank + '</td><td><span class="an-tier t-' + r.tier + '">' + esc(r.tier === "EXCLUIDO" ? "—" : r.tier) + "</span></td>" +
    '<td class="num r"><b>' + r.score + "</b></td>" +
    '<td><div class="an-name">' + esc(r.title) + '</div><div class="meta">' + esc(r.segment.label) + "</div></td>" +
    "<td>" + esc(AN_CHANNEL[r.channel] || r.channel) + "</td>" +
    '<td class="num r">' + fmtInt(r.review_count) + "</td>" +
    '<td class="num r">' + anBRL(r.price.alvo_cents) + '</td><td class="num r meta">' + esc(r.price.faixa_text) + "</td>" +
    "<td>" + (r.outreach_ready ? '<span class="pill ok">Pronto</span>' : flags || '<span class="pill">—</span>') + "</td></tr>";
  if (open) {
    html +=
      '<tr class="an-detail"><td colspan="9"><div class="an-d-grid"><div><h4>Por que esta nota (' + r.score + ")</h4>" +
      (r.factors.length
        ? r.factors.map((f) => '<div class="an-d-f"><span>' + esc(f.label) + '</span><span class="an-btrack"><span class="an-bfill" style="width:' + anPct(f.points, 30) + '%"></span></span><b class="num">+' + f.points + "</b></div>").join("")
        : '<p class="meta">Excluído do ranking: ' + esc(r.flags.map((f) => AN_FLAG[f] || f).join(", ")) + "</p>") +
      '</div><div><h4>Preço sugerido</h4><div class="an-price"><div><span class="meta">Alvo</span><b class="num">' + anBRL(r.price.alvo_cents) + '</b></div><div><span class="meta">Piso interno</span><b class="num">' + anBRL(r.price.piso_cents) +
      '</b></div><div><span class="meta">Falar ao cliente</span><b class="num">' + esc(r.price.faixa_text) + "</b></div></div>" +
      '<p class="meta">' + esc(r.price.scope_name) + " · prazo " + esc(r.price.prazo) + "</p><p class=\"meta\">" + esc(r.price.condicao) + "</p><p class=\"meta\">" + esc(r.price.justificativa) + "</p>" +
      '<div class="d-actions"><button class="btn btn-sm" type="button" data-id="' + r.lead_id + '" data-title="' + esc(r.title) + '" onclick="event.stopPropagation(); anOpenInClients(this)">Abrir em Clientes</button>' +
      (r.whatsapp ? '<button class="btn btn-sm" type="button" onclick="event.stopPropagation(); anCopy(\'' + esc(r.whatsapp) + "', this)\">Copiar número</button>" : "") +
      "</div></div></div></td></tr>";
  }
  return html;
}

function anTable() {
  const rows = anFiltered();
  const segs = AN.data.analytics.by_segment;
  const th = (key, label, cls) => {
    const on = AN.sort.key === key;
    return '<th class="' + (cls || "") + '"><button type="button" class="an-th' + (on ? " on" : "") + '" onclick="anSort(\'' + key + '\')">' + label + (on ? (AN.sort.dir === 1 ? " ↑" : " ↓") : "") + "</button></th>";
  };
  const opts = ['<option value="">Todos os nichos</option>'].concat(segs.map((s) => '<option value="' + esc(s.slug) + '"' + (AN.filters.segment === s.slug ? " selected" : "") + ">" + esc(s.label) + " (" + s.total + ")</option>")).join("");
  const tierOpts = ["", "A", "B", "C", "D", "EXCLUIDO"].map((t) => '<option value="' + t + '"' + (AN.filters.tier === t ? " selected" : "") + ">" + (t ? (t === "EXCLUIDO" ? "Excluídos" : "Tier " + t) : "Todos os tiers") + "</option>").join("");
  return (
    '<div class="an-filters"><select class="an-select" onchange="anFilter(\'segment\', this.value)" aria-label="Nicho">' + opts + '</select>' +
    '<select class="an-select" onchange="anFilter(\'tier\', this.value)" aria-label="Tier">' + tierOpts + "</select>" +
    '<label class="check"><input type="checkbox"' + (AN.filters.ready ? " checked" : "") + ' onchange="anFilter(\'ready\', this.checked)"> Só prontos p/ disparo</label>' +
    '<div class="inline-search-wrap"><input id="an-q" type="search" placeholder="Buscar nome ou número" value="' + esc(AN.filters.q) + '" oninput="anFilter(\'q\', this.value, true)"></div>' +
    '<span class="spacer"></span><span class="meta num">' + rows.length + " lead(s)</span>" +
    '<button class="btn btn-sm" type="button" onclick="anExportCsv()">Exportar CSV</button></div>' +
    '<div class="an-tablewrap"><table class="an-table an-rank"><thead><tr>' +
    th("rank", "#", "r") + "<th>Tier</th>" + th("score", "Nota", "r") + "<th>Lead</th><th>Canal</th>" + th("reviews", "Aval.", "r") + th("price", "Alvo", "r") + '<th class="r">Faixa p/ cliente</th><th>Situação</th></tr></thead><tbody>' +
    (rows.length ? rows.slice(0, AN.shown).map(anRow).join("") : '<tr><td colspan="9"><div class="empty"><strong>Nada com esses filtros</strong>Limpe os filtros para ver todos.</div></td></tr>') +
    "</tbody></table></div>" +
    (rows.length > AN.shown ? '<div class="an-more"><button class="btn btn-sm" type="button" onclick="anShowMore()">Mostrar mais 20 (' + (rows.length - AN.shown) + " restantes)</button></div>" : "")
  );
}

/* ---------- ações ---------- */
function anRefreshTable() {
  if ($("an-table-box")) $("an-table-box").innerHTML = anTable();
  const q = $("an-q");
  if (q && AN._refocus) { q.focus(); q.setSelectionRange(q.value.length, q.value.length); AN._refocus = false; }
  document.querySelectorAll(".an-seg").forEach((el) => el.classList.toggle("on", !!AN.filters.segment && el.dataset.slug === AN.filters.segment));
}
function anFilter(key, value, refocus) { AN.filters[key] = value; AN.shown = 20; AN.openId = null; AN._refocus = !!refocus; anRefreshTable(); }
function anPickSegment(slug) { AN.filters.segment = AN.filters.segment === slug ? "" : slug; AN.shown = 20; AN.openId = null; anRefreshTable(); const el = $("an-table-box"); if (el) el.scrollIntoView({ behavior: "smooth", block: "start" }); }
function anSort(key) { AN.sort = AN.sort.key === key ? { key, dir: -AN.sort.dir } : { key, dir: key === "rank" ? 1 : -1 }; anRefreshTable(); }
function anShowMore() { AN.shown += 20; anRefreshTable(); }
function anToggleRow(id) { AN.openId = AN.openId === id ? null : id; anRefreshTable(); }
function anCopy(text, btn) { navigator.clipboard && navigator.clipboard.writeText(text).then(() => { btn.textContent = "Copiado ✓"; }); }
function anOpenInClients(btn) {
  if (typeof clearAllFilters === "function") clearAllFilters();
  const title = btn.dataset.title || "";
  const id = Number(btn.dataset.id || 0);
  if ($("filter-search")) $("filter-search").value = title;
  if ($("filter-search-inline")) $("filter-search-inline").value = title;
  location.hash = "#clientes";
  if (typeof onFilterChange === "function") onFilterChange();
  if (id && typeof selectLead === "function") selectLead(id, { scroll: true, overlay: true });
}
function anExportCsv() {
  const rows = anFiltered();
  const head = ["rank", "tier", "nota", "nicho", "nome", "whatsapp", "canal", "avaliacoes", "escopo", "preco_alvo", "preco_piso", "faixa_cliente", "pronto"];
  const cell = (v) => '"' + String(v ?? "").replace(/"/g, '""') + '"';
  const lines = [head.join(";")].concat(
    rows.map((r) => [r.rank, r.tier, r.score, r.segment.label, r.title, r.whatsapp, r.channel, r.review_count, r.price.scope_name, r.price.alvo_cents / 100, r.price.piso_cents / 100, r.price.faixa_text, r.outreach_ready ? "sim" : "nao"].map(cell).join(";"))
  );
  const blob = new Blob(["\ufeff" + lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "ranking_leads.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}

/* ---------- view ---------- */
function anKpi(label, value, hint) {
  return '<div class="kpi an-kpi"><span class="kpi-label">' + esc(label) + '</span><span class="kpi-value num">' + value + '</span><span class="an-kpi-hint">' + esc(hint) + "</span></div>";
}

function renderAnalysisView() {
  const box = $("view-analise-body");
  if (!box) return;
  if (AN.loading && !AN.data) { box.innerHTML = '<div class="empty"><strong>Calculando ranking…</strong>Lendo a base de clientes.</div>'; return; }
  if (AN.error) { box.innerHTML = '<div class="empty"><strong>' + esc(AN.error) + '</strong><button class="btn btn-sm" type="button" onclick="loadAnalysis(true)">Tentar de novo</button></div>'; return; }
  if (!AN.data) { loadAnalysis(); return; }

  const d = AN.data, a = d.analytics, s = d.summary;
  const valid = s.total - s.excluded;
  const scores = d.ranking.filter((r) => r.tier !== "EXCLUIDO").map((r) => r.score);
  const avg = scores.length ? (scores.reduce((x, y) => x + y, 0) / scores.length).toFixed(1).replace(".", ",") : "0";
  box.innerHTML =
    '<div class="an-notice">Nota = prioridade de abordagem (0–100), <b>não</b> probabilidade de fechar. Telefone fixo não conta como WhatsApp. ' +
    "Nenhuma mensagem é enviada a partir desta tela.</div>" +
    '<div class="kpi-strip">' +
    anKpi("Leads abordáveis", fmtInt(valid), s.excluded + " excluídos de " + s.total) +
    anKpi("Prontos p/ disparo", fmtInt(s.ready), anPct(s.ready, valid) + "% da base abordável") +
    anKpi("Tier A", fmtInt(s.tiers.A), "disparar primeiro") +
    anKpi("Nota média", avg, "de 100 pontos") +
    anKpi("Valor na mesa", anBRLShort(a.pipeline.ready_value_cents), "soma do preço-alvo dos prontos") +
    "</div>" +
    '<div class="an-cols"><section class="panel"><header><h3>Funil: da base ao disparo</h3></header><p class="meta">Quanto da base realmente pode receber mensagem hoje.</p>' + anFunnel(a.funnel) + "</section>" +
    '<section class="panel"><header><h3>Distribuição das notas</h3></header><p class="meta">Número de leads por faixa de nota, empilhado por tier.</p>' + anHistogram(a.score_histogram) + "</section></div>" +
    '<section class="panel an-block"><header><h3>Nichos: onde está a oportunidade</h3></header><p class="meta">Clique num nicho para filtrar a tabela. A faixa mostra o preço sugerido mínimo, médio e máximo.</p><div class="an-segs">' + anSegments(a.by_segment) + "</div></section>" +
    '<div class="an-cols"><section class="panel"><header><h3>Porte × nota</h3></header><p class="meta">Cada ponto é um lead. Clique para abrir os detalhes na tabela.</p>' + anScatter(d.ranking) + "</section>" +
    '<section class="panel"><header><h3>Dor principal</h3></header><p class="meta">Por que o lead precisa de nós, e a nota média de cada dor.</p>' +
    anBars(a.by_pain, "count", "label", (r) => " · nota " + r.avg_score) + '<h3 class="an-sub">Canal de contato</h3>' +
    anBars(Object.keys(a.reach).map((k) => ({ label: AN_CHANNEL[k] || k, count: a.reach[k] })), "count", "label") + "</section></div>" +
    '<div class="an-cols"><section class="panel"><header><h3>Plano de disparo (20 por dia útil)</h3></header><p class="meta">Melhores primeiro. Só entram prontos (celular, sem duplicata).</p>' + anPlan(a.plan_days) + "</section>" +
    '<section class="panel"><header><h3>Simulador de receita</h3></header>' + anSimulator() + "</section></div>" +
    '<section class="panel an-block"><header><h3>Ranking completo</h3></header><div id="an-table-box">' + anTable() + "</div></section>" +
    '<details class="panel an-block an-details"><summary><b>Metodologia: como ler estes números</b></summary>' + anMethodology(a.methodology) + "</details>";

  document.querySelectorAll(".an-dot").forEach((el) => el.addEventListener("click", () => {
    AN.openId = Number(el.dataset.id);
    AN.filters = { segment: "", tier: "", ready: false, q: "" };
    const rows = anFiltered();
    const idx = rows.findIndex((r) => r.lead_id === AN.openId);
    if (idx >= AN.shown) AN.shown = Math.ceil((idx + 1) / 20) * 20;
    anRefreshTable();
    const tr = document.querySelector('[data-row="' + AN.openId + '"]');
    if (tr) tr.scrollIntoView({ behavior: "smooth", block: "center" });
  }));
}
