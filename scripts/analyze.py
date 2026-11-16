"""Run every region x variable trend test and the corroboration ledger.

Usage: python analyze.py DATA_DIR
Writes DATA_DIR/results.json
"""
import json, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from trend import analyze, to_arrays, deseasonalize

# CERES-era only for radiation/cloud: avoids the SRB -> CERES source splice in POWER.
PERIODS = {"ALLSKY_SFC_SW_DWN": (2001, 2025), "CLOUD_AMT": (2001, 2025)}
DEFAULT = (1981, 2025)
# Below this long-term mean a variable is physically negligible in the region (e.g. trace snow).
MIN_MEAN = {"SNODP": 1.0}

PAIRS = {  # primary POWER variable -> independent corroborating product
    "T2M": ("gistemp", "GISTEMP v4 station + ship temperature"),
    "PRECTOTCORR": ("gpcp", "GPCP v2.3 satellite + gauge precipitation"),
}


def anomaly_corr(a_rows, b_rows):
    common = sorted(set(r[0] for r in a_rows) & set(r[0] for r in b_rows))
    A = [r for r in a_rows if r[0] in common]; B = [r for r in b_rows if r[0] in common]
    _, ma, va, _ = to_arrays(A); _, mb, vb, _ = to_arrays(B)
    aa, _ = deseasonalize(ma, va); ab, _ = deseasonalize(mb, vb)
    return float(np.corrcoef(aa, ab)[0, 1])


def classify(primary, second):
    """OpenPlanter-style claim status: verified / unverified / contradicted."""
    if second is None:
        return "unverified", "Single source: no independent NASA product reduced for this variable yet."
    ps, ss = primary["verdict"] == "significant", second["verdict"] == "significant"
    same = np.sign(primary["slope_decade"]) == np.sign(second["slope_decade"])
    if ps and ss and same:
        return "verified", "Independent product shows a significant trend of the same sign."
    if ss and not same and (ps or primary["verdict"] == "suggestive"):
        return "contradicted", "Independent product shows a significant trend of the opposite sign."
    if not ps and not ss and same:
        return "unverified", "Both products agree in direction, but neither trend is significant."
    if ps and not ss:
        return "unverified", "Primary trend is significant; independent product " + (
            "agrees in sign but is not significant." if same else "points the other way (not significant).")
    if ss and not ps:
        return "unverified", "Independent product is significant, primary is not — collect more years."
    return "unverified", "Products disagree in direction; neither is significant."


def main(data_dir):
    d = Path(data_dir)
    S = json.loads((d / "series.json").read_text())
    C = json.loads((d / "corroboration.json").read_text())
    results, ledger = {}, []
    for reg, vars_ in S["series"].items():
        for var, meta in vars_.items():
            start, end = PERIODS.get(var, DEFAULT)
            r = analyze(meta["data"], start, end)
            if r.get("applicable") and r["mean"] < MIN_MEAN.get(var, -1e9):
                r = dict(applicable=False, reason=f"Long-term mean {r['mean']:.3g} {meta['units']} is negligible here.")
            results.setdefault(reg, {})[var] = r
            if not r.get("applicable"):
                continue
            second = corr = None; src = None
            if var in PAIRS:
                key, label = PAIRS[var]
                rows = C[key]["series"][reg]
                second = analyze(rows, start, end)
                corr = anomaly_corr(meta["data"], rows)
                src = dict(key=key, label=label, product=C[key]["product"], url=C[key]["url"],
                           slope_decade=second["slope_decade"], ci_decade=second["ci_decade"],
                           p_ttest=second["p_ttest"], p_mk=second["p_mk"], verdict=second["verdict"],
                           anomaly_correlation=corr)
            status, why = classify(r, second)
            ledger.append(dict(
                id=f"{reg}:{var}", region=reg, variable=var,
                claim=f"{S['variables'][var]['label']} in {S['regions'][reg]['name']} changed by "
                      f"{r['slope_decade']:+.3g} {meta['units']}/decade ({r['start']}–{r['end']}).",
                status=status, reason=why, primary_verdict=r["verdict"],
                evidence=[dict(source=f"NASA POWER {meta['api']['version']} — {', '.join(meta['sources'])}",
                               url=meta["url"], sha256=meta["sha256"], retrieved=S["fetched_at"])]
                         + ([dict(source=src["product"], url=src["url"], retrieved=C["fetched_at"])] if src else []),
                corroboration=src))
    out = dict(fetched_at=S["fetched_at"], corroboration_fetched_at=C["fetched_at"],
               periods=dict(default=DEFAULT, **PERIODS), results=results, ledger=ledger)
    (d / "results.json").write_text(json.dumps(out, indent=1, default=float))
    from collections import Counter
    print(Counter(x["status"] for x in ledger))
    print(Counter(r["verdict"] for v in results.values() for r in v.values() if r.get("applicable")))


if __name__ == "__main__":
    main(sys.argv[1])
