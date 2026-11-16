/* Earth System Trend Detective — UI. Depends on window.TD (trend.js) and window.DATA (bundled NASA snapshot). */
(function () {
  "use strict";
  const D = window.DATA, TD = window.TD;
  const $ = (s, el = document) => el.querySelector(s);
  const h = (tag, attrs = {}, ...kids) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") el.className = v; else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else if (v !== false && v != null) el.setAttribute(k, v);
    }
    for (const k of kids.flat()) if (k != null) el.append(k.nodeType ? k : document.createTextNode(k));
    return el;
  };
  const NS = "http://www.w3.org/2000/svg";
  const s = (tag, attrs = {}, text) => { const el = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v); if (text != null) el.textContent = text; return el; };
  const esc = (x) => String(x).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const GROUPS = [
    ["Heat", ["T2M", "T2M_MAX"]],
    ["Water", ["PRECTOTCORR", "EVLAND", "GWETROOT"]],
    ["Air", ["QV2M", "RH2M", "WS10M"]],
    ["Sunlight & clouds", ["ALLSKY_SFC_SW_DWN", "CLOUD_AMT"]],
    ["Snow", ["SNODP"]],
  ];
  const SHORT = { T2M: "T", T2M_MAX: "Tmax", PRECTOTCORR: "Rain", EVLAND: "Evap", GWETROOT: "Soil", QV2M: "Hum", RH2M: "RH", WS10M: "Wind", ALLSKY_SFC_SW_DWN: "Sun", CLOUD_AMT: "Cloud", SNODP: "Snow" };
  const MAPLABEL = { svalbard: ["Svalbard", "r"], sahel: ["Sahel", "r"], amazon: ["Amazon", "r"], california: ["California", "r", -4],
    delhi: ["Delhi", "r"], murray: ["Murray–Darling", "l"], sfbay: ["SF Bay", "l", 8] };
  const MXLABEL = { T2M: "Air temp", T2M_MAX: "Max temp", PRECTOTCORR: "Rain", EVLAND: "Evaporation", GWETROOT: "Soil wetness", QV2M: "Spec. humidity",
    RH2M: "Rel. humidity", WS10M: "Wind", ALLSKY_SFC_SW_DWN: "Sunlight", CLOUD_AMT: "Cloud", SNODP: "Snow" };
  const VARS = GROUPS.flatMap((g) => g[1]);
  const REGS = Object.keys(D.regions);
  const period = (v) => D.periods[v] || D.periods.default;
  const MIN_MEAN = { SNODP: 1.0 };

  const state = { region: "svalbard", variable: "T2M", start: null, end: null, mode: "anom", custom: null };

  // ---------- data access ----------
  function expand(ser) {
    const [y0, m0] = ser.s.split("-").map(Number); const out = [];
    ser.v.forEach((v, i) => { if (v == null) return; const k = (m0 - 1) + i; out.push([`${y0 + Math.floor(k / 12)}-${String((k % 12) + 1).padStart(2, "0")}`, v]); });
    return out;
  }
  const cache = new Map();
  function rowsFor(reg, v) {
    const key = reg + ":" + v; if (!cache.has(key)) cache.set(key, expand(D.series[reg][v])); return cache.get(key);
  }
  function corrRows(reg, v) { const c = D.corr[v]; if (!c) return null; const key = "c:" + reg + ":" + v; if (!cache.has(key)) cache.set(key, expand(c.series[reg])); return cache.get(key); }

  function runCase(reg, v, start, end) {
    const [a, b] = period(v); const st = Math.max(start ?? a, a), en = Math.min(end ?? b, b);
    const r = TD.analyze(rowsFor(reg, v), st, en);
    if (r.applicable && r.mean < (MIN_MEAN[v] ?? -Infinity)) return { applicable: false, reason: `Long-term mean ${r.mean.toFixed(3)} ${D.variables[v].units} is negligible here.`, start: st, end: en };
    r.st = st; r.en = en; return r;
  }
  function classify(p, sec) {
    if (!sec || !sec.applicable) return ["unverified", "Single source: no independent product is reduced for this variable yet. Treat as a lead."];
    const ps = p.verdict === "significant", ss = sec.verdict === "significant", same = Math.sign(p.slopeDecade) === Math.sign(sec.slopeDecade);
    if (ps && ss && same) return ["verified", "An independent product shows a significant trend of the same sign."];
    if (ss && !same && (ps || p.verdict === "suggestive")) return ["contradicted", "An independent product shows a significant trend of the opposite sign."];
    if (!ps && !ss && same) return ["unverified", "Both products agree in direction, but neither trend is significant."];
    if (ps && !ss) return ["unverified", "Primary trend is significant; the independent product " + (same ? "agrees in sign but is not significant." : "points the other way (not significant).")];
    if (ss && !ps) return ["unverified", "The independent product is significant but the primary is not. Collect more years."];
    return ["unverified", "Products disagree in direction; neither is significant."];
  }

  // ---------- formatting ----------
  const sig = (x, d = 3) => { if (!isFinite(x)) return "—"; const a = Math.abs(x); if (a === 0) return "0"; const p = a >= 100 ? 0 : a >= 10 ? 1 : a >= 1 ? 2 : Math.min(4, d - 1 - Math.floor(Math.log10(a))); return (x > 0 ? "+" : x < 0 ? "−" : "") + a.toFixed(Math.max(p, 0)); };
  const plain = (x) => sig(x).replace(/^\+/, "");
  const pfmt = (p) => (!isFinite(p) ? "p = —" : p < 0.0001 ? "p < 0.0001" : "p = " + p.toFixed(p < 0.01 ? 4 : 3));
  const units = (v) => (state.custom && v === "custom" ? state.custom.units : D.variables[v].units);

  // ---------- header + controls ----------
  function buildControls() {
    const vwrap = $("#vars"); vwrap.innerHTML = "";
    for (const [g, list] of GROUPS) {
      vwrap.append(h("div", { class: "group-label" }, g));
      vwrap.append(h("div", { class: "chips" }, list.map((v) => h("button", { class: "chip", "data-var": v, "aria-pressed": String(state.variable === v), onclick: () => select({ variable: v, custom: null }) }, D.variables[v].label))));
    }
    const rwrap = $("#regions"); rwrap.innerHTML = "";
    for (const r of REGS) {
      const R = D.regions[r];
      rwrap.append(h("button", { class: "region", "data-reg": r, "aria-pressed": String(state.region === r && !state.custom), onclick: () => select({ region: r, custom: null }) },
        h("span", {}, R.name), h("span", { class: "box" }, `${R.lat[0]}…${R.lat[1]}°, ${R.lon[0]}…${R.lon[1]}°`), h("span", { class: "kind" }, R.kind + " — " + R.why)));
    }
    const ys = $("#ystart"), ye = $("#yend");
    [ys, ye].forEach((sel) => { sel.innerHTML = ""; for (let y = 1981; y <= 2025; y++) sel.append(h("option", { value: y }, y)); });
    ys.onchange = () => select({ start: +ys.value }); ye.onchange = () => select({ end: +ye.value });
    document.querySelectorAll("#mode button").forEach((b) => b.addEventListener("click", () => select({ mode: b.dataset.mode })));
  }
  function syncControls(res) {
    document.querySelectorAll("#vars .chip").forEach((b) => b.setAttribute("aria-pressed", String(!state.custom && b.dataset.var === state.variable)));
    document.querySelectorAll("#regions .region").forEach((b) => b.setAttribute("aria-pressed", String(!state.custom && b.dataset.reg === state.region)));
    document.querySelectorAll("#mode button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === state.mode)));
    const V = state.custom ? state.custom.meta : D.variables[state.variable];
    $("#vardef").innerHTML = `<b>${esc(V.label)}</b> (${esc(V.units)}). ${esc(V.definition)}<br><span class="muted small">Source: ${esc(V.source)}</span>`;
    const [a, b] = state.custom ? [state.custom.y0, state.custom.y1] : period(state.variable);
    ["#ystart", "#yend"].forEach((id) => { [...$(id).options].forEach((o) => { o.disabled = +o.value < a || +o.value > b; }); });
    $("#ystart").value = res.st ?? a; $("#yend").value = res.en ?? b;
    drawMap();
  }

  // ---------- map ----------
  function drawMap() {
    const svg = $("#map"); svg.innerHTML = "";
    const X = (lon) => (lon + 180) * 2, Y = (lat) => (90 - lat) * 2;
    for (let lon = -150; lon <= 150; lon += 30) svg.append(s("line", { class: "grat", x1: X(lon), x2: X(lon), y1: 0, y2: 360 }));
    for (let lat = -60; lat <= 60; lat += 30) svg.append(s("line", { class: "grat", x1: 0, x2: 720, y1: Y(lat), y2: Y(lat) }));
    svg.append(s("path", { class: "land", d: D.land }));
    for (const r of REGS) {
      const R = D.regions[r], sel = !state.custom && r === state.region;
      const pad = 2.5; // enlarge tiny boxes so they stay clickable
      const g = s("g", { tabindex: "0", role: "button", "aria-label": R.name });
      const rect = s("rect", { class: "rbox" + (sel ? " sel" : ""), x: X(R.lon[0]) - pad, y: Y(R.lat[1]) - pad, width: (R.lon[1] - R.lon[0]) * 2 + 2 * pad, height: (R.lat[1] - R.lat[0]) * 2 + 2 * pad, rx: 2 });
      g.append(rect);
      const lab = MAPLABEL[r] || [R.name, "r"];
      const left = lab[1] === "l";
      g.append(s("text", { class: "rlabel", x: left ? X(R.lon[0]) - 6 : X(R.lon[1]) + 6, y: Y((R.lat[0] + R.lat[1]) / 2) + (lab[2] || 4), "text-anchor": left ? "end" : "start" }, lab[0]));
      g.addEventListener("click", () => select({ region: r, custom: null }));
      g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select({ region: r, custom: null }); } });
      svg.append(g);
    }
    if (state.custom && state.custom.box) {
      const b = state.custom.box;
      svg.append(s("rect", { class: "custom", x: X(b.lon[0]) - 2, y: Y(b.lat[1]) - 2, width: (b.lon[1] - b.lon[0]) * 2 + 4, height: (b.lat[1] - b.lat[0]) * 2 + 4 }));
    }
  }

  // ---------- chart ----------
  function running12(t, v) { const out = []; for (let i = 11; i < v.length; i++) { let sum = 0; for (let k = i - 11; k <= i; k++) sum += v[k]; out.push([(t[i] + t[i - 11]) / 2, sum / 12]); } return out; }
  function niceTicks(lo, hi, n = 5) {
    const span = hi - lo || 1, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((x) => x >= step0);
    const out = []; for (let x = Math.ceil(lo / step) * step; x <= hi + 1e-9; x += step) out.push(+x.toPrecision(12)); return { ticks: out, step };
  }
  function drawChart(res, sec, title, u) {
    const svg = $("#chart"); svg.innerHTML = "";
    const W = 900, H = 380, L = 64, R = 18, B = 40; let T = 54;
    if (!res.applicable) { svg.append(s("text", { x: W / 2, y: H / 2, "text-anchor": "middle", class: "title" }, res.reason)); return; }
    const S = res._series, mode = state.mode;
    let base, smooth = null, points = null, trend, band, secLine = null, ylab;
    const tm = S.t.reduce((a, b) => a + b, 0) / S.t.length;
    if (mode === "annual") {
      points = S.annT.map((y, i) => [y + 0.5, S.ann[i]]);
      const am = S.ann.reduce((a, b) => a + b, 0) / S.ann.length, tam = S.annT.reduce((a, b) => a + b, 0) / S.annT.length + 0.5;
      const f = (b) => (t) => am + b * (t - tam);
      trend = f(S.slope); band = [f(S.ci[0]), f(S.ci[1])]; ylab = `Annual mean (${u})`;
    } else if (mode === "raw") {
      base = S.t.map((t, i) => [t, S.v[i]]); smooth = running12(S.t, S.v);
      const vm = S.v.reduce((a, b) => a + b, 0) / S.v.length; const f = (b) => (t) => vm + b * (t - tm);
      trend = f(S.slope); band = [f(S.ci[0]), f(S.ci[1])]; ylab = `Monthly value (${u})`;
    } else {
      base = S.t.map((t, i) => [t, S.anom[i]]); smooth = running12(S.t, S.anom);
      const am = S.anom.reduce((a, b) => a + b, 0) / S.anom.length; const f = (b) => (t) => am + b * (t - tm);
      trend = f(S.slope); band = [f(S.ci[0]), f(S.ci[1])]; ylab = `Anomaly, seasonal cycle removed (${u})`;
      if (sec && sec.applicable) secLine = running12(sec._series.t, sec._series.anom);
    }
    // legend (wraps onto extra rows when it is wider than the plot)
    const items = [];
    if (base) items.push(["raw", "Monthly"]);
    if (smooth) items.push(["smooth", "12-month mean"]);
    if (points) items.push(["pt", "Annual mean"]);
    items.push(["trend", `Linear trend ${sig(res.slopeDecade)} ${u}/decade`]);
    items.push(["band", "95% range of the trend"]);
    if (secLine) items.push(["second", D.corr[state.variable].label + " (12-mo mean)"]);
    const lg = s("g", { class: "legend" }); let lx = L, row = 0;
    items.forEach(([cls, label]) => {
      const wdt = 34 + label.length * 6.6;
      if (lx > L && lx + wdt > W - R) { row++; lx = L; }
      const g = s("g", { transform: `translate(${lx},${36 + row * 18})` });
      if (cls === "band") g.append(s("rect", { class: "band", x: 0, y: -6, width: 18, height: 10, style: "opacity:.35" }));
      else if (cls === "pt") g.append(s("circle", { class: "pt", cx: 9, cy: -1, r: 3 }));
      else g.append(s("line", { class: cls, x1: 0, x2: 18, y1: -1, y2: -1, style: cls === "raw" ? "stroke-width:2" : "" }));
      g.append(s("text", { x: 24, y: 3 }, label)); lg.append(g);
      lx += wdt;
    });
    T = 54 + row * 18;
    const t0 = S.t[0], t1 = S.t[S.t.length - 1];
    const all = [...(base || []), ...(points || []), ...(secLine || [])].map((p) => p[1]);
    [t0, t1].forEach((t) => { all.push(trend(t), band[0](t), band[1](t)); });
    let lo = Math.min(...all), hi = Math.max(...all); const padY = (hi - lo) * 0.06 || 1; lo -= padY; hi += padY;
    const x = (t) => L + (t - t0) / (t1 - t0) * (W - L - R), y = (v) => T + (hi - v) / (hi - lo) * (H - T - B);
    const { ticks, step } = niceTicks(lo, hi, 6);
    const dec = Math.max(0, -Math.floor(Math.log10(step) + 1e-9) + (String(step).includes("25") ? 1 : 0));
    ticks.forEach((v) => { svg.append(s("line", { class: "grid", x1: L, x2: W - R, y1: y(v), y2: y(v) })); svg.append(s("text", { x: L - 8, y: y(v) + 4, "text-anchor": "end" }, Math.abs(v) < step / 1e6 ? "0" : v.toFixed(dec).replace("-", "−"))); });
    if (mode === "anom" && lo < 0 && hi > 0) svg.append(s("line", { class: "zero", x1: L, x2: W - R, y1: y(0), y2: y(0) }));
    const yStep = (t1 - t0) > 30 ? 5 : (t1 - t0) > 12 ? 2 : 1;
    for (let yr = Math.ceil(t0 / yStep) * yStep; yr <= t1; yr += yStep) svg.append(s("text", { x: x(yr), y: H - B + 18, "text-anchor": "middle" }, yr));
    svg.append(s("text", { x: 14, y: T + (H - T - B) / 2, transform: `rotate(-90 14 ${T + (H - T - B) / 2})`, "text-anchor": "middle" }, ylab));
    const path = (pts) => pts.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + " " + y(p[1]).toFixed(1)).join("");
    svg.append(s("path", { class: "band", d: `M${x(t0)} ${y(band[0](t0))} L${x(t1)} ${y(band[0](t1))} L${x(t1)} ${y(band[1](t1))} L${x(t0)} ${y(band[1](t0))} Z` }));
    if (base) svg.append(s("path", { class: "raw", d: path(base) }));
    if (points) points.forEach((p) => svg.append(s("circle", { class: "pt", cx: x(p[0]), cy: y(p[1]), r: 3 })));
    if (secLine) svg.append(s("path", { class: "second", d: path(secLine) }));
    if (smooth) svg.append(s("path", { class: "smooth", d: path(smooth) }));
    svg.append(s("line", { class: "trend", x1: x(t0), x2: x(t1), y1: y(trend(t0)), y2: y(trend(t1)) }));
    const last = smooth ? smooth[smooth.length - 1] : points[points.length - 1];
    svg.append(s("circle", { cx: x(last[0]), cy: y(last[1]), r: 4, fill: "var(--ink)" }));
    svg.append(s("text", { x: L, y: 18, class: "title" }, title));
    svg.append(lg);
  }

  // ---------- verdict + ledger ----------
  function detectiveRead(res, V, u, regName) {
    if (!res.applicable) return res.reason;
    const dir = res.slopeDecade > 0 ? "risen" : "fallen";
    const tot = `${sig(res.totalChange)} ${u}`;
    let txt = `<b>${esc(V.label)}</b> in <b>${esc(regName)}</b> has ${dir} by about <b>${esc(tot)}</b> from ${res.start.slice(0, 4)} to ${res.end.slice(0, 4)}`;
    if (res.pctChange != null && !/°C/.test(u)) txt += ` (${sig(res.pctChange, 2)}% of its average)`;
    txt += ". ";
    if (res.verdict === "significant") txt += "Both tests say this is very unlikely to be random wiggle: the trend is <b>significant</b>.";
    else if (res.verdict === "suggestive") txt += `One test flags it, the other does not: a <b>lead worth following</b>. At this noise level, roughly ${Math.round(res.yearsToDetect)} years of data are needed to detect it reliably.`;
    else txt += `The change is within natural ups and downs: <b>not significant</b>. About ${isFinite(res.yearsToDetect) ? Math.round(res.yearsToDetect) : "∞"} years of data would be needed to detect a trend this small.`;
    return txt;
  }
  function renderVerdict(res, u, V, regName) {
    const el = $("#verdict"); el.innerHTML = "";
    if (!res.applicable) { el.append(h("p", { class: "muted" }, res.reason)); return; }
    const cls = res.verdict.replace(" ", "-");
    el.append(h("div", {}, h("div", { class: "group-label" }, "Rate of change"),
      h("div", { class: "big " + (res.slopeDecade > 0 ? "up" : "down") }, `${sig(res.slopeDecade)}`),
      h("div", { class: "small" }, `${u} per decade · 95% CI ${sig(res.ciDecade[0])} to ${sig(res.ciDecade[1])}`)));
    el.append(h("div", { class: "row" }, h("span", { class: "pill " + cls }, res.verdict === "significant" ? "Significant (p < 0.05, both tests)" : res.verdict === "suggestive" ? "Suggestive (one test)" : "Not significant")));
    const tb = h("table", { class: "stats" });
    const add = (k, v) => tb.append(h("tr", {}, h("td", {}, k), h("td", {}, v)));
    add("Total change over period", `${sig(res.totalChange)} ${u}`);
    add("Linear trend t-test, AR(1)-adjusted", pfmt(res.pTtest));
    add("Seasonal Mann-Kendall test", pfmt(res.pMk));
    add("Seasonal Sen slope", `${sig(res.senDecade)} /decade`);
    add("Mann-Kendall on annual means", pfmt(res.pMkAnnual));
    add("Months · effective sample size", `${res.nMonths} · ${Math.round(res.neff)}`);
    add("Years needed to detect (Weatherhead)", isFinite(res.yearsToDetect) ? Math.round(res.yearsToDetect) + " yr" : "—");
    el.append(tb);
    el.append(h("div", { class: "read", html: "" }));
    el.lastChild.innerHTML = "<span class='group-label'>Detective's read</span><br>" + detectiveRead(res, V, u, regName);
  }
  function renderLedger(res, sec, status, why, ev) {
    const el = $("#ledger"); el.innerHTML = "";
    el.append(h("div", { class: "row" }, h("span", { class: "pill " + status }, status.toUpperCase()), h("span", { class: "small" }, why)));
    ev.forEach((e) => {
      const d = h("div", { class: "evidence " + (e.role === "contradicts" ? "bad" : e.role === "supports" ? "ok" : "warn") });
      d.innerHTML = `<b>${esc(e.role)}</b> · ${esc(e.source)}<br>${e.detail ? esc(e.detail) + "<br>" : ""}<span class="muted">Retrieved ${esc(e.retrieved)}${e.sha ? " · SHA-256 " + esc(e.sha.slice(0, 16)) + "…" : ""}</span><br><a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.url.length > 110 ? e.url.slice(0, 110) + "…" : e.url)}</a>`;
      el.append(d);
    });
    el.append(h("p", { class: "small muted" }, "Leads, not proof: a trend in one product is a claim to corroborate. Verified = an independent NASA product agrees in sign and significance over the same years."));
  }

  // ---------- matrix ----------
  function cellColor(r) {
    if (!r || !r.applicable) return null;
    const up = r.slopeDecade > 0, base = up ? "var(--up)" : "var(--down)";
    if (r.verdict === "significant") return { bg: base, op: 1 };
    if (r.verdict === "suggestive") return { bg: base, op: 0.5 };
    return { bg: "var(--flat)", op: 0.35 };
  }
  function renderMatrix() {
    const el = $("#matrix"); el.innerHTML = "";
    const tb = h("table", { class: "mx" });
    tb.append(h("tr", {}, h("th", {}, ""), VARS.map((v) => h("th", { class: "v", title: D.variables[v].label }, MXLABEL[v]))));
    for (const r of REGS) {
      const tr = h("tr", {}, h("th", {}, D.regions[r].name.split(/[(]/)[0].replace(/ [&–].*/, "")));
      for (const v of VARS) {
        const res = runCase(r, v, state.start, state.end), c = cellColor(res);
        const sel = !state.custom && r === state.region && v === state.variable;
        if (!c) { tr.append(h("td", {}, h("button", { class: "na" + (sel ? " sel" : ""), disabled: true, title: res.reason || "n/a" }, "—"))); continue; }
        const b = h("button", { class: sel ? "sel" : "", title: `${D.regions[r].name} · ${D.variables[v].label}: ${sig(res.slopeDecade)} ${D.variables[v].units}/decade, ${res.verdict}`, style: `background:${c.bg};opacity:${c.op}`, onclick: () => select({ region: r, variable: v, custom: null }) }, res.slopeDecade > 0 ? "▲" : "▼");
        tr.append(h("td", {}, b));
      }
      tb.append(tr);
    }
    el.append(tb);
  }

  // ---------- strongest leads ----------
  function renderLeads() {
    const el = $("#leads"); el.innerHTML = "";
    const list = VARS.map((v) => [v, runCase(state.region, v, state.start, state.end)]).filter(([, r]) => r.applicable)
      .sort((a, b) => Math.abs(b[1].mkZ) - Math.abs(a[1].mkZ)).slice(0, 4);
    el.append(h("div", { class: "group-label" }, "Strongest signals in this region"));
    el.append(h("div", { class: "chips" }, list.map(([v, r]) => h("button", { class: "chip", onclick: () => select({ variable: v, custom: null }) }, `${D.variables[v].label} ${r.slopeDecade > 0 ? "▲" : "▼"}`))));
  }

  // ---------- main render ----------
  function render() {
    let res, sec = null, title, u, V, regName, status, why, ev = [];
    if (state.custom) {
      const c = state.custom; V = c.meta; u = c.units; regName = c.name;
      res = TD.analyze(c.rows, state.start ?? c.y0, state.end ?? c.y1); res.st = state.start ?? c.y0; res.en = state.end ?? c.y1;
      title = `${V.label} · ${c.name}`;
      [status, why] = ["unverified", "User-supplied NASA POWER file, analysed in your browser. Corroborate with an independent product before claiming a trend."];
      ev.push({ role: "primary", source: c.source, retrieved: c.loaded, sha: c.sha, url: c.url || "local file: " + c.file });
    } else {
      V = D.variables[state.variable]; u = V.units; regName = D.regions[state.region].name;
      res = runCase(state.region, state.variable, state.start, state.end);
      title = `${V.label} · ${regName}`;
      const meta = D.series[state.region][state.variable];
      if (D.corr[state.variable] && res.applicable) {
        sec = TD.analyze(corrRows(state.region, state.variable), res.st, res.en);
      }
      [status, why] = res.applicable ? classify(res, sec) : ["unverified", res.reason];
      ev.push({ role: "primary", source: `NASA POWER ${meta.api} — ${meta.sources.join(", ")} (${meta.n} grid points, area-weighted)`, retrieved: D.fetched_at, sha: meta.sha256, url: meta.url,
        detail: res.applicable ? `Trend ${sig(res.slopeDecade)} ${u}/decade, ${res.verdict}` : null });
      if (sec && sec.applicable) {
        const C = D.corr[state.variable];
        const r = TD.corr(...alignAnom(res, sec));
        ev.push({ role: status === "verified" ? "supports" : status === "contradicted" ? "contradicts" : "checked", source: C.product, retrieved: D.corroboration_fetched_at, url: C.url,
          detail: `Trend ${sig(sec.slopeDecade)} ${C.units}/decade (${sec.verdict}); month-to-month anomaly correlation r = ${r.toFixed(2)}` });
      }
    }
    syncControls(res);
    drawChart(res, sec, title, u);
    renderVerdict(res, u, V, regName);
    renderLedger(res, sec, status, why, ev);
    renderMatrix();
    if (!state.custom) renderLeads(); else $("#leads").innerHTML = "";
    window.__lastResult = { state: { ...state, custom: !!state.custom }, res, sec, status };
  }
  function alignAnom(a, b) {
    const ka = new Map(), kb = new Map();
    a._series.t.forEach((t, i) => ka.set(t.toFixed(3), a._series.anom[i])); b._series.t.forEach((t, i) => kb.set(t.toFixed(3), b._series.anom[i]));
    const xa = [], xb = []; ka.forEach((v, k) => { if (kb.has(k)) { xa.push(v); xb.push(kb.get(k)); } }); return [xa, xb];
  }
  function select(patch) {
    if (("variable" in patch || "region" in patch || "custom" in patch) && !("start" in patch)) { patch.start = null; patch.end = null; }
    Object.assign(state, patch);
    if (state.start != null && state.end != null && state.start > state.end - 2) { if ("start" in patch && patch.start != null) state.end = Math.min(state.start + 2, 2025); else state.start = state.end - 2; }
    render();
  }

  // ---------- demonstrations ----------
  const DEMOS = [
    { n: "Demo 1", t: "The Arctic is heating up", d: "Follow one variable to a strong, verified trend, then check what it does to snow.", steps: [
      [{ region: "svalbard", variable: "T2M", mode: "anom" }, "Svalbard, 2 m air temperature from MERRA-2. The seasonal cycle is removed so only the long-term change is left. The trend line climbs about 0.7 °C every decade."],
      [{ region: "svalbard", variable: "T2M", mode: "anom" }, "The dashed orange line is GISTEMP, built from weather stations instead of a model. It tracks MERRA-2 closely (r ≈ 0.86) and is also significant, so the ledger marks the claim VERIFIED."],
      [{ region: "svalbard", variable: "SNODP", mode: "annual" }, "Same place, different variable: snow depth. Annual means fall by about 4 cm per decade. Only one product covers it here, so the ledger keeps it UNVERIFIED: a strong lead, not a proven fact."] ] },
    { n: "Demo 2", t: "Same planet, opposite rain", d: "Precipitation is rising in one region and falling in another.", steps: [
      [{ region: "sahel", variable: "PRECTOTCORR", mode: "anom" }, "Central Sahel rainfall: recovering from the 1980s droughts, about +0.12 mm/day per decade. GPCP (satellites + rain gauges) agrees: VERIFIED."],
      [{ region: "amazon", variable: "PRECTOTCORR", mode: "anom" }, "Southern Amazon rainfall moves the opposite way and is also VERIFIED by GPCP. MERRA-2's decline is about twice GPCP's, so the direction is solid but the size is uncertain."],
      [{ region: "amazon", variable: "GWETROOT", mode: "anom" }, "Follow the water: Amazon root-zone soil wetness is falling too. Scroll to the map of changes below to see every region and variable at once."] ] },
    { n: "Demo 3", t: "When the evidence disagrees", d: "A significant claim that an independent source contradicts.", steps: [
      [{ region: "delhi", variable: "T2M_MAX", mode: "anom" }, "Delhi daily maximum temperature in MERRA-2 is falling, and that trend is significant. Case closed? Not yet."],
      [{ region: "delhi", variable: "T2M", mode: "anom" }, "For mean temperature, GISTEMP's weather stations show significant warming (about +0.24 °C per decade) while MERRA-2 drifts cooler. The ledger marks this CONTRADICTED."],
      [{ region: "delhi", variable: "ALLSKY_SFC_SW_DWN", mode: "anom" }, "Leads to test next: sunlight reaching the ground fell sharply in CERES data, and humidity rose. Haze and irrigation are possible causes. They are hypotheses until other evidence is checked."] ] },
    { n: "Demo 4", t: "A trend that needs more time", d: "Why 'not significant' is not the same as 'no change'.", steps: [
      [{ region: "sfbay", variable: "PRECTOTCORR", mode: "anom" }, "San Francisco Bay–Delta rainfall trends down, but wet and dry years swing wildly. The t-test is not significant, while the Mann-Kendall test is: SUGGESTIVE."],
      [{ region: "sfbay", variable: "PRECTOTCORR", mode: "annual", start: 2000, end: 2025 }, "Shorten the record to 2000–2025 and the trend almost disappears (it even flips to a tiny rise) and neither test is significant. Short, noisy records can't settle the question: 'years needed to detect' shows how long the record must be."] ] },
  ];
  let tour = null;
  function playStep() {
    const d = DEMOS[tour.i], [patch, cap] = d.steps[tour.j];
    const p = { start: null, end: null, custom: null, ...patch };
    Object.assign(state, p); render();
    $("#tour-text").textContent = `${d.n} · step ${tour.j + 1} of ${d.steps.length}: ${cap}`;
    $("#tour").classList.add("on");
    $("#tour-next").textContent = tour.j + 1 < d.steps.length ? "Next step" : "Finish";
    document.getElementById("case").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  }
  function buildDemos() {
    const el = $("#demos");
    DEMOS.forEach((d, i) => el.append(h("button", { class: "demo", onclick: () => { tour = { i, j: 0 }; playStep(); } }, h("span", { class: "n" }, d.n + " · " + d.steps.length + " steps"), h("h3", {}, d.t), h("span", { class: "small muted" }, d.d))));
    $("#tour-next").onclick = () => { if (!tour) return; if (++tour.j >= DEMOS[tour.i].steps.length) { tour = null; $("#tour").classList.remove("on"); } else playStep(); };
    $("#tour-close").onclick = () => { tour = null; $("#tour").classList.remove("on"); };
  }

  // ---------- bring your own NASA data ----------
  function buildByod() {
    const sel = $("#b-param"); VARS.forEach((v) => sel.append(h("option", { value: v }, `${D.variables[v].label} (${v})`)));
    const upd = () => {
      const g = (id) => $(id).value;
      const u = `https://power.larc.nasa.gov/api/temporal/monthly/regional?parameters=${g("#b-param")}&community=AG&latitude-min=${g("#b-lat0")}&latitude-max=${g("#b-lat1")}&longitude-min=${g("#b-lon0")}&longitude-max=${g("#b-lon1")}&start=${g("#b-y0")}&end=${g("#b-y1")}&format=JSON`;
      $("#b-url").textContent = u; $("#b-open").href = u;
      const dl = Math.abs(g("#b-lat1") - g("#b-lat0")), dn = Math.abs(g("#b-lon1") - g("#b-lon0"));
      $("#b-warn").textContent = dl < 2 || dn < 2 || dl > 10 || dn > 10 ? "NASA POWER regional requests need a box 2° to 10° on each side. For a single point, use the point API and drop that file here too." : "";
    };
    document.querySelectorAll(".byod input, .byod select").forEach((x) => x.addEventListener("input", upd)); upd();
    $("#b-copy").onclick = async () => { try { await navigator.clipboard.writeText($("#b-url").textContent); $("#b-copy").textContent = "Copied"; } catch { $("#b-copy").textContent = "Select the link and copy it"; } };
    const drop = $("#drop"), file = $("#b-file");
    ["dragover", "dragenter"].forEach((e) => drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.add("over"); }));
    ["dragleave", "drop"].forEach((e) => drop.addEventListener(e, () => drop.classList.remove("over")));
    drop.addEventListener("drop", (ev) => { ev.preventDefault(); if (ev.dataTransfer.files[0]) loadFile(ev.dataTransfer.files[0]); });
    file.addEventListener("change", () => file.files[0] && loadFile(file.files[0]));
  }
  async function loadFile(f) {
    const msg = $("#b-msg");
    try {
      const buf = await f.arrayBuffer(); const txt = new TextDecoder().decode(buf); const doc = JSON.parse(txt);
      let sha = ""; try { const dg = await crypto.subtle.digest("SHA-256", buf); sha = [...new Uint8Array(dg)].map((b) => b.toString(16).padStart(2, "0")).join(""); } catch { /* digest unavailable */ }
      const feats = doc.features || (doc.properties ? [doc] : null); if (!feats) throw new Error("This is not a NASA POWER JSON file (no features).");
      const param = Object.keys(doc.parameters || feats[0].properties.parameter)[0];
      const fill = doc.header?.fill_value ?? -999, sums = {}, wts = {}; const lats = [], lons = [];
      feats.forEach((ft) => { const [lon, lat] = ft.geometry.coordinates; lats.push(lat); lons.push(lon); const w = Math.cos(lat * Math.PI / 180);
        for (const [k, v] of Object.entries(ft.properties.parameter[param])) { if (k.endsWith("13") || v == null || v === fill) continue; sums[k] = (sums[k] || 0) + w * v; wts[k] = (wts[k] || 0) + w; } });
      const rows = Object.keys(sums).sort().map((k) => [`${k.slice(0, 4)}-${k.slice(4)}`, sums[k] / wts[k]]);
      if (rows.length < 36) throw new Error("Need monthly data with at least 3 years. Use the monthly API, not daily.");
      const pmeta = (doc.parameters || {})[param] || {};
      const known = D.variables[param];
      state.custom = { rows, file: f.name, sha, loaded: new Date().toISOString().slice(0, 19) + "Z", units: pmeta.units || known?.units || "",
        meta: { label: known?.label || pmeta.longname || param, units: pmeta.units || known?.units || "", definition: known?.definition || pmeta.longname || "", source: (doc.header?.sources || []).join(", ") || "NASA POWER" },
        source: `NASA POWER ${doc.header?.api?.version || ""} — ${(doc.header?.sources || []).join(", ")} · ${feats.length} grid points (your file ${f.name})`,
        name: `Your region ${Math.min(...lats)}…${Math.max(...lats)}°, ${Math.min(...lons)}…${Math.max(...lons)}°`,
        box: { lat: [Math.min(...lats), Math.max(...lats)], lon: [Math.min(...lons), Math.max(...lons)] },
        y0: +rows[0][0].slice(0, 4), y1: +rows[rows.length - 1][0].slice(0, 4) };
      state.start = null; state.end = null; msg.textContent = `Loaded ${f.name}: ${param}, ${rows.length} months, ${feats.length} grid points.`;
      render(); document.getElementById("case").scrollIntoView({ block: "start" });
    } catch (e) { msg.textContent = "Could not read that file: " + e.message; }
  }

  // ---------- evidence graph (OpenPlanter) ----------
  function renderGraph() {
    const G = D.graph, svg = $("#graph"); svg.innerHTML = "";
    const W = 640, H = 300, px = (x) => 20 + (x - 2) / 76 * (W - 40), py = (y) => 16 + (y - 1) / 27 * (H - 32);
    const pos = Object.fromEntries(G.nodes.map((n) => [n.id, [px(n.x), py(n.y)]]));
    G.edges.forEach((e) => svg.append(s("line", { x1: pos[e.source][0], y1: pos[e.source][1], x2: pos[e.target][0], y2: pos[e.target][1] })));
    const col = (n) => n.status === "verified" ? "var(--ok)" : n.status === "contradicted" ? "var(--bad)" : n.status === "unverified" ? "var(--warn)" : n.category === "decoys" ? "var(--flat)" : "var(--accent)";
    G.nodes.forEach((n) => {
      const g = s("g"); const [x, y] = pos[n.id]; const src = !n.status;
      g.append(s("circle", { cx: x, cy: y, r: src ? 9 : 5, fill: col(n), stroke: "var(--panel)", "stroke-width": 1.5 }));
      const t = s("title", {}, n.title); g.append(t);
      const right = x > W * 0.55;
      if (src) g.append(s("text", { x: right ? x - 12 : x + 12, y: y + 4, "text-anchor": right ? "end" : "start", style: "font-weight:600" }, n.id.replace(/ \(decoy.*\)/, " (decoy)")));
      svg.append(g);
    });
    const ev = G.evaluation;
    $("#graph-eval").innerHTML = `Parsed with OpenPlanter's <span class="mono">agent/wiki_graph.py</span>: ${ev.parsed_edges} edges found, ${ev.intended_edges} intended. Precision ${(ev.precision * 100).toFixed(0)}%, recall ${(ev.recall * 100).toFixed(0)}%, ${ev.decoy_edges.length} links to the decoy entry. Every edge traces to a cited line in a finding document.`;
  }

  // ---------- boot ----------
  $("#snap").innerHTML = `NASA POWER snapshot retrieved <b>${esc(D.fetched_at.replace("+00:00", " UTC").replace("T", " "))}</b><br>GISTEMP v4 + GPCP v2.3 retrieved <b>${esc(D.corroboration_fetched_at.replace("+00:00", " UTC").replace("T", " "))}</b>`;
  buildControls(); buildDemos(); buildByod(); renderGraph();
  const hashDemo = location.hash.match(/^#demo-(\d)(?:-(\d))?$/);
  if (hashDemo) { tour = { i: +hashDemo[1] - 1, j: +(hashDemo[2] || 1) - 1 }; playStep(); } else render();
  window.TDApp = { select, state, DEMOS, playDemo: (i, j = 0) => { tour = { i, j }; playStep(); } };
})();
