// Browser stats core (app/trend.js) vs Python pipeline (data/results.json).
import { createRequire } from "module"; import fs from "fs";
const require = createRequire(import.meta.url);
const TD = require("../app/trend.js");
const S = JSON.parse(fs.readFileSync(new URL("../data/series.json", import.meta.url)));
const R = JSON.parse(fs.readFileSync(new URL("../data/results.json", import.meta.url)));
const per = (v) => R.periods[v] || R.periods.default;
const rel = (a, b) => Math.abs(a - b) / Math.max(Math.abs(b), 1e-12);
let n = 0, worst = {};
const upd = (k, x) => { worst[k] = Math.max(worst[k] || 0, x); };
for (const [reg, vs] of Object.entries(S.series)) for (const [v, meta] of Object.entries(vs)) {
  const py = R.results[reg][v]; if (!py.applicable) continue;
  const [a, b] = per(v); const js = TD.analyze(meta.data, a, b);
  upd("slope", rel(js.slopeDecade, py.slope_decade)); upd("ci", rel(js.ciDecade[0], py.ci_decade[0]));
  upd("sen", rel(js.senDecade, py.sen_decade)); upd("neff", rel(js.neff, py.neff));
  if (py.p_ttest > 1e-8) upd("p_t", rel(js.pTtest, py.p_ttest));
  if (py.p_mk > 1e-8) upd("p_mk", rel(js.pMk, py.p_mk));
  upd("ytd", rel(js.yearsToDetect, py.years_to_detect));
  if (js.verdict !== py.verdict) upd("verdict_mismatch", 1);
  n++;
}
console.log(n, "series; worst relative differences:", Object.fromEntries(Object.entries(worst).map(([k, x]) => [k, x.toExponential(2)])));
if (worst.verdict_mismatch || worst.slope > 1e-9 || worst.p_t > 1e-5 || worst.p_mk > 1e-5 || worst.ci > 1e-6) { console.log("FAIL"); process.exit(1); }
console.log("PASS: browser statistics reproduce the Python pipeline.");
