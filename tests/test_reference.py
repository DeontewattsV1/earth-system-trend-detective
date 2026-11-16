"""Check scripts/trend.py against independent reference implementations."""
import json, sys
from pathlib import Path
import numpy as np, pymannkendall as pmk, statsmodels.api as sm
from scipy import stats
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from trend import to_arrays, deseasonalize, ols_ar1, seasonal_mann_kendall, mann_kendall, sen_slope

S = json.loads((ROOT / "data/series.json").read_text())
worst = dict(slope=0, se=0, smk_z=0, smk_sen=0, mk_p=0, sen=0)
n = 0
for reg, vs in S["series"].items():
    for var, meta in vs.items():
        y, m, v, t = to_arrays(meta["data"])
        if np.std(v) < 1e-9: continue
        a, _ = deseasonalize(m, v)
        o = ols_ar1(t, a)
        fit = sm.OLS(a, sm.add_constant(t)).fit()
        worst["slope"] = max(worst["slope"], abs(o["slope"] - fit.params[1]) / abs(fit.params[1]))
        worst["se"] = max(worst["se"], abs(o["se"] - fit.bse[1]) / fit.bse[1])
        # seasonal MK: pymannkendall expects a regular monthly series (period=12)
        # pymannkendall expects a regular grid: rebuild it with NaN in missing months
        idx = (y - y[0]) * 12 + (m - m[0]); full = np.full(idx.max() + 1, np.nan); full[idx] = v
        ref = pmk.seasonal_test(full, period=12)
        smk = seasonal_mann_kendall(y, m, v)
        worst["smk_z"] = max(worst["smk_z"], abs(smk["z"] - ref.z))
        worst["smk_sen"] = max(worst["smk_sen"], abs(smk["sen"] - ref.slope) / max(abs(ref.slope), 1e-9) if ref.slope else abs(smk["sen"]))
        yrs = sorted(set(y)); ann = np.array([v[y == k].mean() for k in yrs if (y == k).sum() == 12])
        r2 = pmk.original_test(ann); mk = mann_kendall(ann)
        worst["mk_p"] = max(worst["mk_p"], abs(mk["p"] - r2.p))
        worst["sen"] = max(worst["sen"], abs(sen_slope(np.arange(len(ann), dtype=float), ann) - r2.slope))
        n += 1
print(f"{n} series checked; worst discrepancies:", {k: f"{x:.2e}" for k, x in worst.items()})
assert worst["slope"] < 1e-9 and worst["se"] < 1e-9 and worst["smk_z"] < 1e-6 and worst["mk_p"] < 1e-9 and worst["sen"] < 1e-9
assert worst["smk_sen"] < 1e-6
print("PASS: OLS (statsmodels), seasonal & annual Mann-Kendall + Sen slope (pymannkendall) all match.")
