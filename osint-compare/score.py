"""Claim-level scoring of each tool's answer against inputs/results.json (via ledger.csv).
Step 1: gpt-4.1-mini extracts atomic claims as JSON (temperature 0). Step 2: deterministic checks against the ledger.
Key from env (OPENAI_API_KEY). Writes scoring/<tool>.claims.json and scoring/scores.json."""
import csv, json, math, os, re, sys, requests
L = {r["id"]: r for r in csv.DictReader(open("inputs/ledger.csv"))}
LOWER = {k.lower(): k for k in L}
ANSWERS = {"openplanter": "runs/openplanter/answer.md", "openplanter_obs60k": "runs/openplanter_obs60k/answer.md", "gptr_local": "runs/gptr_local/report.md",
           "gptr_openaleph": "runs/gptr_aleph/report.md", "flowsint_A_select_all": "runs/flowsint/answer_A_select_all.md",
           "flowsint_B_selected": "runs/flowsint/answer_B_select_non_unverified.md", "gptr_web": "runs/gptr_web/report.md"}
PROMPT = """Extract every atomic factual claim from the REPORT below about specific ledger rows. Ledger row ids look like region:VARIABLE
(regions: svalbard, sahel, amazon, california, delhi, murray, sfbay; variables e.g. T2M, T2M_MAX, PRECTOTCORR, GWETROOT, EVLAND, RH2M, QV2M, WS10M, ALLSKY_SFC_SW_DWN, CLOUD_AMT, SNODP).
Infer the row id from context (e.g. "Sahel air temperature" -> sahel:T2M; "precipitation" -> PRECTOTCORR; "max temperature" -> T2M_MAX). Return JSON {"claims":[...]} where each claim is:
{"text": short quote, "row_id": "region:VARIABLE" or null, "kind": "numeric"|"status"|"other",
 "field": for numeric one of "slope_decade","p_ttest","p_mk","corr_slope_decade","corr_p_ttest","anomaly_correlation" (corr_* = the independent/corroborating product GISTEMP/GPCP),
 "value": number for numeric claims (signed, per decade; p-values as decimals),
 "asserted": for status claims one of "verified_robust","contradicted","unverified","chance_or_artifact","primary_significant","primary_not_significant","primary_suggestive","corroboration_significant","corroboration_not_significant"}.
One claim per number and one per status assertion. Use kind "other" for general statements (methods, caveats, advice) that are not about one row's numbers/status; include at most 15 "other" claims, only factual ones (not advice).
REPORT:
"""
def extract(text):
    r = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
        json={"model": "gpt-4.1-mini", "temperature": 0, "response_format": {"type": "json_object"},
              "messages": [{"role": "user", "content": PROMPT + text}]}, timeout=180)
    r.raise_for_status(); j = r.json()
    return json.loads(j["choices"][0]["message"]["content"])["claims"], j["usage"]
def num(x):
    try: return float(x)
    except: return None
def close(c, t, field):
    if c is None or t is None: return False
    if field.startswith("p_") or field.endswith("p_ttest"):
        if t < 1e-3 and c < 1e-3: return abs(math.log10(c) - math.log10(t)) <= 0.05
        return abs(c - t) <= max(0.06 * abs(t), 0.0006)
    if (c > 0) != (t > 0) and abs(t) > 1e-9: return False
    return abs(c - t) <= max(0.02 * abs(t), 0.0006)
def check(cl):
    rid = (cl.get("row_id") or "").strip(); rid = LOWER.get(rid.lower(), rid)
    if cl.get("kind") == "other" or not rid: return "unverifiable", "not tied to a ledger row"
    if rid not in L: return "wrong", f"row {rid} does not exist"
    row = L[rid]
    if cl["kind"] == "numeric":
        f = cl.get("field"); t = num(row.get(f)) if f in row else None
        if t is None: return "wrong", f"{rid} has no {f} (empty in ledger)"
        return ("correct" if close(num(cl.get("value")), t, f) else "wrong"), f"ledger {f}={row[f]}"
    a = cl.get("asserted"); st, pv, cv = row["status"], row["primary_verdict"], row["corr_verdict"]
    if a == "verified_robust": return ("correct" if st == "verified" else "wrong"), f"status={st}"
    if a == "contradicted": return ("correct" if st == "contradicted" else "wrong"), f"status={st}"
    if a == "unverified": return ("correct" if st == "unverified" else "wrong"), f"status={st}"
    if a == "primary_significant": return ("correct" if pv == "significant" else "wrong"), f"primary={pv}"
    if a == "primary_not_significant": return ("correct" if pv == "not significant" else "wrong"), f"primary={pv}"
    if a == "primary_suggestive": return ("correct" if pv == "suggestive" else "wrong"), f"primary={pv}"
    if a == "corroboration_significant": return ("correct" if cv == "significant" else "wrong"), f"corr={cv or 'none'}"
    if a == "corroboration_not_significant": return ("correct" if cv in ("not significant", "suggestive") else "wrong"), f"corr={cv or 'none'}"
    if a == "chance_or_artifact":
        if st == "verified": return "wrong", "row is verified"
        if st == "contradicted" or pv in ("not significant", "suggestive"): return "correct", f"status={st}, primary={pv}"
        return "unverifiable", f"status={st}, primary={pv}: ledger does not say chance/artifact"
    return "unverifiable", f"unknown assertion {a}"
VERIFIED = {k for k, r in L.items() if r["status"] == "verified"}
out = {}; usage_tot = {"prompt_tokens": 0, "completion_tokens": 0}
for tool, path in ANSWERS.items():
    text = open(path).read()
    cf = f"scoring/{tool}.claims.json"
    if os.path.exists(cf) and not os.environ.get("REEXTRACT"):  # reuse cached extraction (re-check only)
        claims = json.load(open(cf))
    else:
        claims, u = extract(text)
        for k in usage_tot: usage_tot[k] += u.get(k, 0)
    for c in claims: c["check"], c["why"] = check(c)
    json.dump(claims, open(f"scoring/{tool}.claims.json", "w"), indent=1)
    cnt = {k: sum(1 for c in claims if c["check"] == k) for k in ("correct", "wrong", "unverifiable")}
    robust_named = {LOWER.get((c.get("row_id") or "").lower()) for c in claims if c.get("asserted") == "verified_robust"} - {None}
    cites = set(re.findall(r"\b(svalbard|sahel|amazon|california|delhi|murray|sfbay):([A-Z0-9_]+)", text))
    out[tool] = dict(claims=len(claims), **cnt,
        numeric_checked=sum(1 for c in claims if c["kind"] == "numeric"),
        numeric_wrong=sum(1 for c in claims if c["kind"] == "numeric" and c["check"] == "wrong"),
        robust_recall=f"{len(robust_named & VERIFIED)}/{len(VERIFIED)}", robust_false=sorted(robust_named - VERIFIED),
        delhi_contradiction_flagged=any(LOWER.get((c.get('row_id') or '').lower()) == "delhi:T2M" and c.get("asserted") == "contradicted" and c["check"] == "correct" for c in claims),
        multiple_testing_mentioned=bool(re.search(r"multiple (testing|comparison)|72 tests|expected by chance|3[–-]4 (significant|false)|false[- ]positive", text, re.I)),
        explicit_row_id_citations=len(cites), words=len(text.split()))
    print(tool, out[tool])
prev = json.load(open("scoring/scores.json")) if os.path.exists("scoring/scores.json") else {}
for k in usage_tot: usage_tot[k] += prev.get("extraction_usage", {}).get(k, 0)
json.dump(dict(scores=out, extraction_usage=usage_tot, extraction_cost_usd=round(usage_tot["prompt_tokens"] * 0.4e-6 + usage_tot["completion_tokens"] * 1.6e-6, 4)), open("scoring/scores.json", "w"), indent=1)
print(usage_tot)
