"""Flowsint run: import the evidence ledger as a graph (Flowsint JSON import API), then ask Flowsint's AI chat the shared task
with node context built exactly like the UI's formatContext (nodeLabel strings). OpenAI key -> Flowsint vault via /api/keys/create.
Keys: OPENAI_API_KEY (env), Flowsint local user password FS_USER_PW (env, from ~/.secrets/flowsint-local.env)."""
import json, os, sys, time, requests
B = "http://127.0.0.1:5001/api"; OUT = "runs/flowsint"; os.makedirs(OUT, exist_ok=True)
d = json.load(open("inputs/results.json")); task = open("TASK.txt").read().strip()
EMAIL = "etd-local@example.com"; PW = os.environ["FS_USER_PW"]
s = requests.Session()
s.post(f"{B}/auth/register", json={"email": EMAIL, "password": PW})
tok = s.post(f"{B}/auth/token", data={"username": EMAIL, "password": PW}).json()["access_token"]
s.headers["Authorization"] = f"Bearer {tok}"
names = [k["name"] for k in s.get(f"{B}/keys").json()]
if "OPENAI_API_KEY" not in names:
    r = s.post(f"{B}/keys/create", json={"name": "OPENAI_API_KEY", "key": os.environ["OPENAI_API_KEY"]}); r.raise_for_status()
inv = s.post(f"{B}/investigations/create", json={"name": "ETD evidence ledger", "description": "NASA Space Apps ETD"})
if inv.status_code >= 400: inv = s.post(f"{B}/investigations", json={"name": "ETD evidence ledger", "description": "NASA Space Apps ETD"})
inv = inv.json(); print("investigation", inv.get("id"))
sk = s.post(f"{B}/sketches/create", json={"title": "ETD ledger graph", "description": "72-row evidence ledger", "investigation_id": inv["id"]}).json(); print("sketch", sk.get("id"))
def g(v): return f"{v:+.3g}" if isinstance(v, float) else "na"
def p(v): return f"{v:.2g}" if isinstance(v, float) else "na"
nodes, edges = [], []
PROD = {"merra2": "NASA POWER MERRA-2/CERES (primary)", "gistemp": "GISTEMP v4 (independent)", "gpcp": "GPCP v2.3 (independent)"}
for k, v in PROD.items(): nodes.append(dict(id=k, type="organization", label=v))
for reg in d["results"]: nodes.append(dict(id="reg:" + reg, type="phrase", label="Region " + reg))
for x in d["ledger"]:
    r = d["results"][x["region"]].get(x["variable"], {}); c = x.get("corroboration") or {}
    lab = f'{x["id"]} {x["status"]}; {g(r.get("slope_decade"))}/dec p={p(r.get("p_ttest"))}'
    if c: lab += f'; {c["key"]} {g(c.get("slope_decade"))} p={p(c.get("p_ttest"))}'
    lab = lab[:100]
    nodes.append(dict(id=x["id"], type="phrase", label=lab))
    edges.append(dict(source=x["id"], target="reg:" + x["region"], label="IN_REGION"))
    edges.append(dict(source=x["id"], target="merra2", label="MEASURED_BY"))
    if c: edges.append(dict(source=x["id"], target=c["key"], label={"verified": "CORROBORATED_BY", "contradicted": "CONTRADICTED_BY"}.get(x["status"], "COMPARED_WITH")))
imp = {"nodes": nodes, "edges": edges}; json.dump(imp, open(f"{OUT}/import_graph.json", "w"), indent=1)
t0 = time.time()
an = s.post(f"{B}/sketches/{sk['id']}/import/analyze", files={"file": ("ledger_graph.json", json.dumps(imp), "application/json")}); an.raise_for_status(); an = an.json()
maps = []
for et, ent in an["entities"].items():
    for res in ent["results"]:
        maps.append(dict(id=res["node_id"], node_id=res["node_id"], entity_type=et, nodeLabel=res["obj"].get("nodeLabel"), data=res["obj"], include=True))
ex = s.post(f"{B}/sketches/{sk['id']}/import/execute", data={"entity_mappings_json": json.dumps({"nodes": maps, "edges": [dict(from_id=e["from_id"], to_id=e["to_id"], label=e["label"]) for e in an.get("edges", [])]})})
print("import", ex.status_code, ex.text[:300]); time.sleep(2)
graph = s.get(f"{B}/sketches/{sk['id']}/graph").json(); json.dump(graph, open(f"{OUT}/graph_readback.json", "w"), indent=1)
gn = graph.get("nds") or graph.get("nodes") or []; ge = graph.get("rls") or graph.get("edges") or graph.get("relationships") or []
print("graph nodes", len(gn), "edges", len(ge))
def lbl(n): return n.get("nodeLabel") or (n.get("data") or {}).get("nodeLabel") or n.get("label")
results = {}
variants = {"A_select_all": [lbl(n) for n in gn],
            "B_select_non_unverified": [lbl(n) for n in gn if lbl(n) and (" verified;" in lbl(n) or " contradicted;" in lbl(n))]}
for name, ctx in variants.items():
    chat = s.post(f"{B}/chats/create", json={"title": f"ETD {name}", "investigation_id": inv["id"]}).json()
    t = time.time(); r = s.post(f"{B}/chats/stream/{chat['id']}", json={"prompt": task, "context": ctx}, stream=True)
    raw = r.text; dt = round(time.time() - t, 1)
    msgs = s.get(f"{B}/chats/{chat['id']}").json().get("messages", [])
    bot = [m["content"] for m in msgs if m["is_bot"]]
    ctx_str = "Context: " + "; ".join(ctx)
    results[name] = dict(http=r.status_code, seconds=dt, n_context_items=len(ctx), context_chars=len(ctx_str), context_truncated_at_2000=len(ctx_str) > 2000,
                         context_seen_by_llm=(ctx_str[:2000] + "...") if len(ctx_str) > 2000 else ctx_str)
    ans = bot[-1] if bot else raw
    open(f"{OUT}/answer_{name}.md", "w").write(ans if isinstance(ans, str) else json.dumps(ans))
    open(f"{OUT}/stream_{name}.txt", "w").write(raw)
    print(name, r.status_code, dt, len(ctx), len(ctx_str))
json.dump(dict(import_seconds=round(time.time() - t0, 1), import_response=ex.json() if ex.ok else ex.text, graph_nodes=len(gn), graph_edges=len(ge), chats=results), open(f"{OUT}/meta.json", "w"), indent=1)
