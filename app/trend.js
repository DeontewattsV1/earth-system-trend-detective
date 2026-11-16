/* Earth System Trend Detective — statistics core (browser + Node).
   Same formulas as scripts/trend.py; tests/test_parity.mjs checks agreement. */
(function (root) {
  "use strict";

  // ---------- special functions ----------
  function erfc(x) { // Numerical Recipes erfcc, fractional error < 1.2e-7 everywhere
    const z = Math.abs(x), t = 1 / (1 + 0.5 * z);
    const r = t * Math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 +
      t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277)))))))));
    return x >= 0 ? r : 2 - r;
  }
  const normSf = (z) => 0.5 * erfc(z / Math.SQRT2);

  function lgamma(x) { // Lanczos
    const g = 7, c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
      -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - lgamma(1 - x);
    x -= 1; let a = c[0]; const t = x + g + 0.5;
    for (let i = 1; i < 9; i++) a += c[i] / (x + i);
    return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
  }
  function betacf(a, b, x) {
    const MAXIT = 300, EPS = 1e-15, FPMIN = 1e-300;
    let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN; d = 1 / d; let h = d;
    for (let m = 1; m <= MAXIT; m++) {
      const m2 = 2 * m; let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d; const del = d * c; h *= del; if (Math.abs(del - 1) < EPS) break;
    }
    return h;
  }
  function ibeta(a, b, x) { // regularized incomplete beta I_x(a,b)
    if (x <= 0) return 0; if (x >= 1) return 1;
    const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b;
  }
  const tSf2 = (t, df) => ibeta(df / 2, 0.5, df / (df + t * t)); // two-sided P(|T|>t)
  function tPpf(p, df) { // inverse CDF by bisection on two-sided tail
    const tail = 2 * (1 - p); let lo = 0, hi = 1e3;
    for (let i = 0; i < 200; i++) { const mid = (lo + hi) / 2; if (tSf2(mid, df) > tail) lo = mid; else hi = mid; }
    return (lo + hi) / 2;
  }

  // ---------- helpers ----------
  const sign = (x) => (x > 0 ? 1 : x < 0 ? -1 : 0);
  const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;
  function median(a) { const s = Float64Array.from(a).sort(); const n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; }
  function corr(a, b) { const ma = mean(a), mb = mean(b); let sab = 0, saa = 0, sbb = 0;
    for (let i = 0; i < a.length; i++) { sab += (a[i] - ma) * (b[i] - mb); saa += (a[i] - ma) ** 2; sbb += (b[i] - mb) ** 2; }
    return sab / Math.sqrt(saa * sbb); }

  function toArrays(rows) {
    const y = [], m = [], v = [], t = [];
    for (const [k, val] of rows) { const yy = +k.slice(0, 4), mm = +k.slice(5, 7); y.push(yy); m.push(mm); v.push(val); t.push(yy + (mm - 0.5) / 12); }
    return { y, m, v, t };
  }
  function deseasonalize(m, v) {
    const s = new Array(13).fill(0), c = new Array(13).fill(0);
    m.forEach((k, i) => { s[k] += v[i]; c[k]++; });
    const clim = s.map((x, k) => (c[k] ? x / c[k] : NaN));
    return { anom: v.map((x, i) => x - clim[m[i]]), clim };
  }

  function olsAr1(t, a, alpha = 0.05) {
    const n = a.length, tm = mean(t), am = mean(a);
    let sxx = 0, sxy = 0;
    for (let i = 0; i < n; i++) { sxx += (t[i] - tm) ** 2; sxy += (t[i] - tm) * (a[i] - am); }
    const b = sxy / sxx, c = am - b * tm;
    const e = a.map((x, i) => x - (b * t[i] + c));
    const sse = e.reduce((s, x) => s + x * x, 0);
    const se = Math.sqrt(sse / (n - 2) / sxx);
    const r1 = corr(e.slice(0, -1), e.slice(1));
    const r1c = Math.min(Math.max(r1, 0), 0.99);
    let neff = n * (1 - r1c) / (1 + r1c); neff = Math.max(Math.min(neff, n), 3);
    const seAdj = neff > 2 ? se * Math.sqrt((n - 2) / (neff - 2)) : Infinity;
    const df = neff - 2, tstat = b / seAdj, p = tSf2(Math.abs(tstat), df), tcrit = tPpf(1 - alpha / 2, df);
    return { slope: b, intercept: c, se, seAdj, r1, n, neff, t: tstat, p, ci: [b - tcrit * seAdj, b + tcrit * seAdj],
      residSd: Math.sqrt(sse / (n - 2)) };
  }

  function mkSVar(x) {
    const n = x.length; let s = 0;
    for (let i = 0; i < n - 1; i++) for (let j = i + 1; j < n; j++) s += sign(x[j] - x[i]);
    const counts = new Map(); x.forEach((v) => counts.set(v, (counts.get(v) || 0) + 1));
    let tie = 0; counts.forEach((c) => { tie += c * (c - 1) * (2 * c + 5); });
    return { s, v: (n * (n - 1) * (2 * n + 5) - tie) / 18 };
  }
  const zScore = (s, v) => (v <= 0 ? 0 : s > 0 ? (s - 1) / Math.sqrt(v) : s < 0 ? (s + 1) / Math.sqrt(v) : 0);
  function mannKendall(x) { const { s, v } = mkSVar(x); const z = zScore(s, v); return { S: s, var: v, z, p: 2 * normSf(Math.abs(z)) }; }

  function seasonalMK(y, m, v) {
    let S = 0, V = 0; const slopes = [];
    for (let k = 1; k <= 12; k++) {
      const x = [], yr = [];
      m.forEach((mm, i) => { if (mm === k) { x.push(v[i]); yr.push(y[i]); } });
      if (x.length < 3) continue;
      const r = mkSVar(x); S += r.s; V += r.v;
      for (let i = 0; i < x.length - 1; i++) for (let j = i + 1; j < x.length; j++) { const dy = yr[j] - yr[i]; if (dy) slopes.push((x[j] - x[i]) / dy); }
    }
    const z = zScore(S, V);
    return { S, var: V, z, p: 2 * normSf(Math.abs(z)), sen: median(slopes) };
  }
  function senSlope(t, x) { const s = []; for (let i = 0; i < x.length - 1; i++) for (let j = i + 1; j < x.length; j++) s.push((x[j] - x[i]) / (t[j] - t[i])); return median(s); }

  function yearsToDetect(slope, sd, r1) {
    if (!slope) return Infinity; const phi = Math.min(Math.max(r1, 0), 0.99);
    return Math.pow((3.3 * sd / Math.abs(slope)) * Math.sqrt((1 + phi) / (1 - phi)), 2 / 3);
  }
  function verdict(pt, pmk) {
    if (pt < 0.05 && pmk < 0.05) return "significant";
    if (pt < 0.05 || pmk < 0.05 || (pt < 0.10 && pmk < 0.10)) return "suggestive";
    return "not significant";
  }

  function analyze(rowsAll, start, end) {
    const rows = rowsAll.filter((r) => (start == null || +r[0].slice(0, 4) >= start) && (end == null || +r[0].slice(0, 4) <= end));
    if (rows.length < 36) return { applicable: false, reason: "Need at least 3 years of monthly data." };
    const { y, m, v, t } = toArrays(rows);
    const vm = mean(v); if (Math.sqrt(mean(v.map((x) => (x - vm) ** 2))) < 1e-9) return { applicable: false, reason: "Variable is constant here." };
    const { anom, clim } = deseasonalize(m, v);
    const o = olsAr1(t, anom), smk = seasonalMK(y, m, v);
    const yrs = [...new Set(y)], annT = [], ann = [];
    yrs.forEach((k) => { const sel = v.filter((_, i) => y[i] === k); if (sel.length === 12) { annT.push(k); ann.push(mean(sel)); } });
    const amk = ann.length >= 3 ? mannKendall(ann) : { p: NaN };
    const span = t[t.length - 1] - t[0];
    return {
      applicable: true, start: rows[0][0], end: rows[rows.length - 1][0], nMonths: v.length, mean: vm,
      slopeDecade: o.slope * 10, ciDecade: [o.ci[0] * 10, o.ci[1] * 10], pTtest: o.p, r1: o.r1, neff: o.neff,
      senDecade: smk.sen * 10, pMk: smk.p, mkZ: smk.z, pMkAnnual: amk.p, senAnnualDecade: ann.length >= 3 ? senSlope(annT, ann) * 10 : NaN,
      totalChange: o.slope * span, pctChange: Math.abs(vm) > 1e-6 ? (o.slope * span) / Math.abs(vm) * 100 : null,
      yearsToDetect: yearsToDetect(o.slope, o.residSd, o.r1), verdict: verdict(o.p, smk.p),
      _series: { y, m, v, t, anom, clim, intercept: o.intercept, slope: o.slope, ci: o.ci, annT, ann },
    };
  }

  const api = { analyze, olsAr1, seasonalMK, mannKendall, senSlope, deseasonalize, toArrays, tSf2, tPpf, normSf, corr, verdict, yearsToDetect };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.TD = api;
})(typeof window !== "undefined" ? window : globalThis);
