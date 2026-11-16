"""Bundle the app into one self-contained HTML file with the NASA data snapshot.

Usage: python build_app.py DATA_DIR APP_DIR LAND_GEOJSON OUT_HTML
"""
import json, sys
from pathlib import Path

data_dir, app_dir, land_path, out = map(Path, sys.argv[1:5])
S = json.loads((data_dir / "series.json").read_text())
C = json.loads((data_dir / "corroboration.json").read_text())
R = json.loads((data_dir / "results.json").read_text())
G = json.loads((data_dir / "evidence_graph.json").read_text())


def compact(rows):
    """[[YYYY-MM, v], ...] -> start + contiguous values with null for gaps."""
    y0, m0 = map(int, rows[0][0].split("-"))
    idx = {r[0]: r[1] for r in rows}
    y1, m1 = map(int, rows[-1][0].split("-"))
    vals = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        vals.append(idx.get(f"{y}-{m:02d}"))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return dict(s=rows[0][0], v=vals)


variables = {}
for k, v in S["variables"].items():
    api_units = S["series"]["svalbard"][k]["units"]
    units = {"C": "°C", "MJ/m^2/day": "MJ/m²/day", "1": "fraction (0–1)"}.get(api_units, api_units)
    variables[k] = dict(label=v["label"], units=units, definition=v["definition"], source=v["source"])

series = {reg: {var: dict(compact(m["data"]), url=m["url"], sha256=m["sha256"], api=m["api"]["version"],
                          sources=m["sources"], n=m["n_gridpoints"]) for var, m in vs.items()}
          for reg, vs in S["series"].items()}
corr = {
    "T2M": dict(label="GISTEMP v4 stations", product=C["gistemp"]["product"], url=C["gistemp"]["url"], units="°C",
                series={r: compact(x) for r, x in C["gistemp"]["series"].items()}),
    "PRECTOTCORR": dict(label="GPCP v2.3 satellite + gauge", product=C["gpcp"]["product"], url=C["gpcp"]["url"], units="mm/day",
                        series={r: compact(x) for r, x in C["gpcp"]["series"].items()}),
}

# Natural Earth 110 m land -> equirectangular SVG path (viewBox 720 x 360)
land = json.loads(land_path.read_text())
parts = []
for f in land["features"]:
    g = f["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        for ring in poly:
            pts, last = [], None
            for lon, lat in ring:
                p = (round((lon + 180) * 2, 1), round((90 - lat) * 2, 1))
                if p != last:
                    pts.append(p); last = p
            if len(pts) > 2:
                parts.append("M" + "L".join(f"{x:g} {y:g}" for x, y in pts) + "Z")

DATA = dict(fetched_at=S["fetched_at"], corroboration_fetched_at=C["fetched_at"],
            regions={k: {kk: v[kk] for kk in ("name", "lat", "lon", "kind", "why")} for k, v in S["regions"].items()},
            variables=variables, periods={k: v for k, v in R["periods"].items()},
            series=series, corr=corr, graph=G, land="".join(parts))

html = (app_dir / "index.src.html").read_text()
html = html.replace("/*CSS*/", (app_dir / "style.css").read_text())
html = html.replace("/*DATA*/", "window.DATA=" + json.dumps(DATA, separators=(",", ":"), ensure_ascii=False) + ";")
html = html.replace("/*TREND*/", (app_dir / "trend.js").read_text())
html = html.replace("/*APP*/", (app_dir / "app.js").read_text())
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html)
print("wrote", out, f"{len(html) / 1e6:.2f} MB")
