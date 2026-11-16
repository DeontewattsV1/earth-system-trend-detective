"""Flatten results.json ledger (72 rows) to inputs/ledger.csv + ledger.md, so text-only tools see the full ledger."""
import json, csv, sys
d = json.load(open("inputs/results.json"))
rows = []
for x in d["ledger"]:
    reg, var = x["region"], x["variable"]
    r = d["results"][reg].get(var, {})
    c = x.get("corroboration") or {}
    rows.append(dict(id=x["id"], region=reg, variable=var, status=x["status"], primary_verdict=x["primary_verdict"],
        slope_decade=r.get("slope_decade"), p_ttest=r.get("p_ttest"), p_mk=r.get("p_mk"), period=f'{r.get("start")}..{r.get("end")}',
        corroborating_product=c.get("key"), corr_slope_decade=c.get("slope_decade"), corr_p_ttest=c.get("p_ttest"),
        corr_verdict=c.get("verdict"), anomaly_correlation=c.get("anomaly_correlation"), reason=x["reason"], claim=x["claim"]))
def f(v):
    return f"{v:.4g}" if isinstance(v, float) else ("" if v is None else str(v))
with open("inputs/ledger.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); [w.writerow({k: f(v) for k, v in r.items()}) for r in rows]
with open("inputs/ledger.md", "w") as fh:
    fh.write("# Evidence ledger (72 rows, from results.json)\n\nPeriods: " + json.dumps(d["periods"]) + "\n\n")
    for r in rows:
        fh.write(f"## {r['id']}\n" + "\n".join(f"- {k}: {f(v)}" for k, v in r.items() if k != "id") + "\n\n")
print(len(rows))
