// Recompute the numbers quoted in the demo captions from the bundled data.
import fs from "fs"; import vm from "vm";
const html = fs.readFileSync(new URL("../dist/index.html", import.meta.url), "utf8");
const ctx = { window: {}, globalThis: {} }; vm.createContext(ctx);
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
vm.runInContext(scripts[0], ctx); vm.runInContext(scripts[1].replace("typeof window !== \"undefined\" ? window : globalThis", "window"), ctx);
const D = ctx.window.DATA, TD = ctx.window.TD;
const expand = (ser) => { const [y0, m0] = ser.s.split("-").map(Number); const o = []; ser.v.forEach((v, i) => { if (v == null) return; const k = m0 - 1 + i; o.push([`${y0 + Math.floor(k / 12)}-${String(k % 12 + 1).padStart(2, "0")}`, v]); }); return o; };
const run = (r, v, a, b) => { const [pa, pb] = D.periods[v] || D.periods.default; return TD.analyze(expand(D.series[r][v]), a ?? pa, b ?? pb); };
const sec = (r, v, a = 1981, b = 2025) => TD.analyze(expand(D.corr[v].series[r]), a, b);
const f = (x) => ({ slope: +x.slopeDecade.toFixed(3), ci: x.ciDecade.map((c) => +c.toFixed(3)), pt: +x.pTtest.toPrecision(3), pmk: +x.pMk.toPrecision(3), verdict: x.verdict, ytd: Math.round(x.yearsToDetect), total: +x.totalChange.toFixed(2) });
const cases = {
  "svalbard T2M": f(run("svalbard", "T2M")), "svalbard T2M GISTEMP": f(sec("svalbard", "T2M")), "svalbard SNODP": f(run("svalbard", "SNODP")),
  "sahel PRECIP": f(run("sahel", "PRECTOTCORR")), "sahel PRECIP GPCP": f(sec("sahel", "PRECTOTCORR")),
  "amazon PRECIP": f(run("amazon", "PRECTOTCORR")), "amazon PRECIP GPCP": f(sec("amazon", "PRECTOTCORR")), "amazon GWETROOT": f(run("amazon", "GWETROOT")),
  "delhi T2M_MAX": f(run("delhi", "T2M_MAX")), "delhi T2M": f(run("delhi", "T2M")), "delhi T2M GISTEMP": f(sec("delhi", "T2M")),
  "delhi ALLSKY": f(run("delhi", "ALLSKY_SFC_SW_DWN")), "delhi RH2M": f(run("delhi", "RH2M")),
  "sfbay PRECIP": f(run("sfbay", "PRECTOTCORR")), "sfbay PRECIP 2000-2025": f(run("sfbay", "PRECTOTCORR", 2000, 2025)),
};
for (const [k, v] of Object.entries(cases)) console.log(k.padEnd(24), JSON.stringify(v));
