"""Trend statistics used by Earth System Trend Detective.

The browser app (app/trend.js) implements the same formulas; tests/test_parity.py
checks that the two agree, and tests/test_reference.py checks this module against
scipy / statsmodels / pymannkendall.
"""
import math
import numpy as np
from scipy import stats


def to_arrays(rows):
    """rows: [["YYYY-MM", value], ...] -> years, months (1-12), values, decimal time."""
    y = np.array([int(r[0][:4]) for r in rows]); m = np.array([int(r[0][5:7]) for r in rows])
    v = np.array([r[1] for r in rows], dtype=float)
    return y, m, v, y + (m - 0.5) / 12.0


def deseasonalize(m, v):
    """Anomaly = value minus that calendar month's mean over the analysed period."""
    clim = {k: v[m == k].mean() for k in range(1, 13) if (m == k).any()}
    return v - np.array([clim[k] for k in m]), clim


def ols_ar1(t, a, alpha=0.05):
    """OLS slope with lag-1 autocorrelation correction (Santer et al., 2000)."""
    n = len(a)
    tm, am = t.mean(), a.mean()
    sxx = ((t - tm) ** 2).sum()
    b = ((t - tm) * (a - am)).sum() / sxx
    c = am - b * tm
    e = a - (b * t + c)
    se = math.sqrt((e ** 2).sum() / (n - 2) / sxx)
    r1 = float(np.corrcoef(e[:-1], e[1:])[0, 1])
    r1c = min(max(r1, 0.0), 0.99)
    neff = n * (1 - r1c) / (1 + r1c)
    neff = max(min(neff, n), 3.0)
    se_adj = se * math.sqrt((n - 2) / (neff - 2)) if neff > 2 else float("inf")
    dof = neff - 2
    tstat = b / se_adj
    p = 2 * stats.t.sf(abs(tstat), dof)
    tcrit = stats.t.ppf(1 - alpha / 2, dof)
    return dict(slope=b, intercept=c, se=se, se_adj=se_adj, r1=r1, n=n, neff=neff,
                t=tstat, p=p, ci=(b - tcrit * se_adj, b + tcrit * se_adj),
                resid_sd=float(e.std(ddof=2)))


def _mk_s_var(x):
    n = len(x)
    s = 0
    for i in range(n - 1):
        s += np.sign(x[i + 1:] - x[i]).sum()
    _, counts = np.unique(x, return_counts=True)
    var = (n * (n - 1) * (2 * n + 5) - (counts * (counts - 1) * (2 * counts + 5)).sum()) / 18.0
    return float(s), float(var)


def _z(s, var):
    if var <= 0:
        return 0.0
    return (s - 1) / math.sqrt(var) if s > 0 else (s + 1) / math.sqrt(var) if s < 0 else 0.0


def mann_kendall(x):
    s, var = _mk_s_var(np.asarray(x, float))
    z = _z(s, var)
    return dict(S=s, var=var, z=z, p=2 * stats.norm.sf(abs(z)))


def seasonal_mann_kendall(years, months, v):
    """Hirsch et al. (1982) seasonal Kendall test + seasonal Sen slope (units / year)."""
    S = VAR = 0.0
    slopes = []
    for k in range(1, 13):
        sel = months == k
        if sel.sum() < 3:
            continue
        x, yr = v[sel], years[sel]
        s, var = _mk_s_var(x)
        S += s; VAR += var
        for i in range(len(x) - 1):
            dy = yr[i + 1:] - yr[i]
            slopes.extend(((x[i + 1:] - x[i]) / dy)[dy != 0])
    z = _z(S, VAR)
    return dict(S=S, var=VAR, z=z, p=2 * stats.norm.sf(abs(z)), sen=float(np.median(slopes)))


def sen_slope(t, x):
    i, j = np.triu_indices(len(x), 1)
    return float(np.median((x[j] - x[i]) / (t[j] - t[i])))


def years_to_detect(slope_per_year, resid_sd, r1):
    """Weatherhead et al. (1998): years of monthly data needed to detect the trend (p≈0.05, 90% power)."""
    if slope_per_year == 0:
        return float("inf")
    phi = min(max(r1, 0.0), 0.99)
    return ((3.3 * resid_sd / abs(slope_per_year)) * math.sqrt((1 + phi) / (1 - phi))) ** (2 / 3)


def verdict(p_t, p_mk):
    if p_t < 0.05 and p_mk < 0.05:
        return "significant"
    if p_t < 0.05 or p_mk < 0.05 or (p_t < 0.10 and p_mk < 0.10):
        return "suggestive"
    return "not significant"


def analyze(rows, start=None, end=None):
    rows = [r for r in rows if (start is None or int(r[0][:4]) >= start) and (end is None or int(r[0][:4]) <= end)]
    y, m, v, t = to_arrays(rows)
    if np.nanstd(v) < 1e-9:
        return dict(applicable=False, reason="Variable is constant here (e.g. no snow ever recorded).")
    a, clim = deseasonalize(m, v)
    o = ols_ar1(t, a)
    smk = seasonal_mann_kendall(y, m, v)
    yrs = sorted(set(y.tolist()))
    ann = np.array([v[y == k].mean() for k in yrs if (y == k).sum() == 12])
    ann_t = np.array([k for k in yrs if (y == k).sum() == 12], float)
    amk = mann_kendall(ann)
    span = t[-1] - t[0]
    mean = float(v.mean())
    return dict(
        applicable=True, start=rows[0][0], end=rows[-1][0], n_months=len(v), mean=mean,
        slope_decade=o["slope"] * 10, ci_decade=[o["ci"][0] * 10, o["ci"][1] * 10],
        p_ttest=o["p"], r1=o["r1"], neff=o["neff"],
        sen_decade=smk["sen"] * 10, p_mk=smk["p"], mk_z=smk["z"],
        p_mk_annual=amk["p"], sen_annual_decade=sen_slope(ann_t, ann) * 10,
        total_change=o["slope"] * span,
        pct_change=(o["slope"] * span / abs(mean) * 100) if abs(mean) > 1e-6 else None,
        years_to_detect=years_to_detect(o["slope"], o["resid_sd"], o["r1"]),
        verdict=verdict(o["p"], smk["p"]),
    )
