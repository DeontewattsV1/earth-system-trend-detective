"""Write an OpenPlanter-format evidence wiki and build its graph with OpenPlanter's own parser.

Usage: python build_wiki.py DATA_DIR WIKI_DIR OPENPLANTER_REPO
  * WIKI_DIR/index.md + source docs follow OpenPlanter's wiki/template.md
  * Each trend finding is a wiki entry whose Cross-Reference Potential section names
    (in **bold**) the sources that support or contradict it.
  * agent.wiki_graph.WikiGraphModel (OpenPlanter, MIT) parses the wiki into a graph.
  * We score that graph against the edges we intended (precision / recall) — a small
    version of the "misleading name match" test.
Writes DATA_DIR/evidence_graph.json
"""
import json, sys
from pathlib import Path

data_dir, wiki, repo = map(Path, sys.argv[1:4])
sys.path.insert(0, str(repo))
from agent.wiki_graph import WikiGraphModel  # noqa: E402

R = json.loads((data_dir / "results.json").read_text())
S = json.loads((data_dir / "series.json").read_text())
C = json.loads((data_dir / "corroboration.json").read_text())

SOURCES = {
    "merra2": dict(name="NASA POWER MERRA-2 Reanalysis", cat="NASA Models", jur="Global, 0.5° x 0.625°",
                   file="models/power-merra2.md",
                   summary="NASA POWER serves monthly variables from NASA GMAO's MERRA-2 reanalysis: a weather model continuously corrected by satellite and in-situ observations.",
                   access="REST API, no login: https://power.larc.nasa.gov/api/temporal/monthly/regional (one parameter per call, 2°–10° boxes).",
                   quality="Reanalysis is a model product: trends can be affected by changes in the observing system and by missing processes (e.g. irrigation).",
                   xref=["**GISTEMP v4 Station Temperature** for 2 m temperature", "**GPCP v2.3 Precipitation** for precipitation"]),
    "ceres": dict(name="NASA POWER CERES SYN1deg Radiation", cat="NASA Satellites", jur="Global, 1°",
                  file="satellites/power-ceres.md",
                  summary="Surface sunlight and cloud amount from NASA's CERES instruments (Terra/Aqua) via the SYN1deg product; GEWEX SRB before 2001.",
                  access="Same NASA POWER API (parameters ALLSKY_SFC_SW_DWN, CLOUD_AMT).",
                  quality="Source changes from SRB to CERES in 2001; this project analyses 2001–2025 only to avoid the splice.",
                  xref=["**NASA POWER MERRA-2 Reanalysis** shares the API but not the retrieval"]),
    "gistemp": dict(name="GISTEMP v4 Station Temperature", cat="NASA Station Records", jur="Global, 2° grid",
                    file="stations/gistemp.md",
                    summary="NASA GISS Surface Temperature Analysis: GHCNv4 weather stations over land plus ERSSTv5 ship/buoy sea-surface temperature, 1200 km smoothing.",
                    access="https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz (netCDF, no login).",
                    quality="Sparse stations at high latitude and in parts of Africa; values are anomalies vs 1951–1980.",
                    xref=["**NASA POWER MERRA-2 Reanalysis** (independent check of T2M)"]),
    "gpcp": dict(name="GPCP v2.3 Precipitation", cat="NASA Satellites", jur="Global, 2.5° grid",
                 file="satellites/gpcp.md",
                 summary="Global Precipitation Climatology Project monthly analysis (NASA GSFC / University of Maryland) merging satellite estimates with rain gauges.",
                 access="https://www.ncei.noaa.gov/data/global-precipitation-climatology-project-gpcp-monthly/access/ (netCDF per month).",
                 quality="Coarse 2.5° cells; small regions are covered by 1–4 cells. MERRA-2 corrected precipitation is partly nudged toward observations, so agreement is not fully independent.",
                 xref=["**NASA POWER MERRA-2 Reanalysis** (independent check of PRECTOTCORR)"]),
}
VAR_SOURCE = {v: ("ceres" if v in ("ALLSKY_SFC_SW_DWN", "CLOUD_AMT") else "merra2") for v in S["variables"]}
PAIR = {"T2M": "gistemp", "PRECTOTCORR": "gpcp"}
HEADLINE = {("delhi", "ALLSKY_SFC_SW_DWN"), ("svalbard", "SNODP"), ("amazon", "GWETROOT"),
            ("sahel", "GWETROOT"), ("delhi", "RH2M"), ("amazon", "CLOUD_AMT")}


def source_doc(s):
    return f"""# {s['name']}

## Summary

{s['summary']}

## Access Methods

{s['access']}

## Data Schema

Monthly values keyed YYYYMM per grid point; this project averages grid points with cos(latitude) area weights.

## Coverage

- **Jurisdiction**: {s['jur']}
- **Time range**: 1981–2025 analysed
- **Update frequency**: Monthly

## Cross-Reference Potential

""" + "\n".join(f"- {x}" for x in s["xref"]) + """

## Data Quality

""" + s["quality"] + "\n"


wiki.mkdir(parents=True, exist_ok=True)
for s in SOURCES.values():
    p = wiki / s["file"]; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(source_doc(s))

findings, intended = [], set()
# Source-to-source links written in the source docs are intended too.
intended |= {frozenset((SOURCES["merra2"]["name"], SOURCES[k]["name"])) for k in ("gistemp", "gpcp", "ceres")}
# Decoy entry with a confusable name: any edge to it is a misleading name match.
DECOY = dict(name="MERRA-2 Aerosol Diagnostics (decoy, not used)", file="decoys/merra2-aerosol.md")
(wiki / "decoys").mkdir(parents=True, exist_ok=True)
(wiki / DECOY["file"]).write_text("# MERRA-2 Aerosol Diagnostics\n\n## Summary\n\nDecoy entry for the misleading-name-match test. Not used by any finding.\n\n## Cross-Reference Potential\n\nNone.\n")
for item in R["ledger"]:
    reg, var = item["region"], item["variable"]
    if var not in PAIR and (reg, var) not in HEADLINE:
        continue
    r = R["results"][reg][var]
    name = f"Finding {reg}-{var}"
    prim = SOURCES[VAR_SOURCE[var]]["name"]
    refs = [f"- Supported by **{prim}**: slope {r['slope_decade']:+.3g} per decade, t-test p={r['p_ttest']:.2g}, Mann-Kendall p={r['p_mk']:.2g}."]
    intended.add(frozenset((name, prim)))
    c = item["corroboration"]
    if c:
        sec = SOURCES[PAIR[var]]["name"]
        verb = {"verified": "Corroborated by", "contradicted": "Contradicted by"}.get(item["status"], "Checked against")
        refs.append(f"- {verb} **{sec}**: slope {c['slope_decade']:+.3g} per decade ({c['verdict']}), anomaly correlation r={c['anomaly_correlation']:.2f}.")
        intended.add(frozenset((name, sec)))
    rel = f"findings/{reg}-{var.lower()}.md"
    (wiki / "findings").mkdir(exist_ok=True)
    (wiki / rel).write_text(f"""# {item['claim']}

## Summary

Status: **{item['status'].upper()}** — {item['reason']}

## Cross-Reference Potential

""" + "\n".join(refs) + f"""

## Data Quality

Primary verdict: {item['primary_verdict']}. Retrieved {item['evidence'][0]['retrieved']}; SHA-256 {item['evidence'][0]['sha256'][:16]}…
""")
    findings.append(dict(name=name, rel=rel, item=item))

cats = {}
for s in SOURCES.values():
    cats.setdefault(s["cat"], []).append(f"| {s['name']} | {s['jur']} | [{Path(s['file']).name}]({s['file']}) |")
cats["Decoys"] = [f"| {DECOY['name']} | Test only | [merra2-aerosol.md]({DECOY['file']}) |"]
cats["Trend Findings"] = [f"| {f['name']} | {S['regions'][f['item']['region']]['name']} | [{Path(f['rel']).name}]({f['rel']}) |" for f in findings]
idx = "# Earth System Trend Detective — Evidence Wiki\n\nOpenPlanter-format wiki: every node is a source or a claim; every edge must trace to a cited passage.\n\n## Sources by Category\n"
for c, rows in cats.items():
    idx += f"\n### {c}\n\n| Source | Jurisdiction | Link |\n|--------|-------------|------|\n" + "\n".join(rows) + "\n"
(wiki / "index.md").write_text(idx)

model = WikiGraphModel(wiki); g = model.graph
found = {frozenset(e) for e in g.edges()}
tp = len(found & intended)
precision = tp / len(found) if found else 0.0
recall = tp / len(intended) if intended else 0.0
spurious = [sorted(e) for e in found - intended]
status = {f["name"]: f["item"]["status"] for f in findings}
out = dict(
    parser="OpenPlanter agent/wiki_graph.py WikiGraphModel (MIT)",
    nodes=[dict(id=n, category=d["category"], title=d["title"], path=d["path"], status=status.get(n),
                x=round(model.layout[n][0], 2), y=round(model.layout[n][1], 2)) for n, d in g.nodes(data=True)],
    edges=[dict(source=a, target=b, ref_text=d.get("ref_text"), intended=frozenset((a, b)) in intended) for a, b, d in g.edges(data=True)],
    evaluation=dict(intended_edges=len(intended), parsed_edges=len(found), true_positive=tp,
                    precision=precision, recall=recall, spurious=spurious,
                    missed=[sorted(e) for e in intended - found],
                    decoy_edges=[sorted(e) for e in found if DECOY["name"] in e]))
(data_dir / "evidence_graph.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out["evaluation"], indent=1))
