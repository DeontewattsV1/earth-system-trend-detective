"""OpenAleph step of the GPT Researcher–OpenAleph pipeline: create a collection, ingest the shared inputs through
OpenAleph's ingest API (ingest-file workers), wait for processing, then run a fixed query list and export the hits'
extracted text as the corpus GPT Researcher synthesizes from. Key: ALEPH_API_KEY (env)."""
import json, os, time, glob, requests
B = "http://127.0.0.1:8000/api/2"; OUT = "runs/openaleph"; H = {"Authorization": "ApiKey " + os.environ["ALEPH_API_KEY"]}
os.makedirs(f"{OUT}/hits_corpus", exist_ok=True)
t0 = time.time()
col = requests.post(f"{B}/collections", headers=H, json={"label": "ETD evidence ledger", "category": "other", "foreign_id": f"etd_{int(t0)}"}).json()
cid = col.get("id") or col["collection_id"]; print("collection", cid)
files = sorted(glob.glob("inputs/wiki/**/*.md", recursive=True)) + ["inputs/ledger.md", "inputs/ledger.csv", "inputs/results.json", "inputs/evidence_graph.json"]
up = []
for f in files:
    r = requests.post(f"{B}/collections/{cid}/ingest", headers=H, files={"file": (os.path.relpath(f, "inputs").replace("/", "__"), open(f, "rb"))},
                      data={"meta": json.dumps({"file_name": os.path.relpath(f, "inputs"), "languages": ["eng"]})})
    up.append((f, r.status_code))
print("uploaded", len(up), set(s for _, s in up))
for i in range(120):
    st = requests.get(f"{B}/collections/{cid}/status", headers=H).json()
    if i > 3 and not st.get("pending") and not st.get("running"): break
    time.sleep(5)
ingest_s = round(time.time() - t0, 1); print("status", json.dumps(st)[:300], ingest_s)
ents = requests.get(f"{B}/search", headers=H, params={"filter:collection_id": cid, "limit": 200}).json()
schemas = {}
for e in ents["results"]: schemas[e["schema"]] = schemas.get(e["schema"], 0) + 1
QUERIES = ["verified", "contradicted", "significant", "\"not significant\"", "suggestive", "unverified", "GISTEMP", "GPCP", "corroborated", "artifact OR chance"]
hits = {}; qlog = {}
for q in QUERIES:
    r = requests.get(f"{B}/search", headers=H, params={"q": q, "filter:collection_id": cid, "limit": 50}).json()
    qlog[q] = [(e["id"], (e["properties"].get("fileName") or e["properties"].get("title") or [""])[0], e["schema"]) for e in r["results"]]
    for e in r["results"]: hits[e["id"]] = e
docs = {}
for eid, e in hits.items():
    full = requests.get(f"{B}/entities/{eid}", headers=H, params={"excludes": ""}).json()
    p = full.get("properties", {})
    name = (p.get("fileName") or p.get("title") or [eid])[0]
    text = "\n".join(p.get("bodyText", []) or p.get("indexText", []) or [])
    if not text and full.get("schema") in ("Table", "Row"):
        text = json.dumps(p.get("cells", p), ensure_ascii=False)
    if not text:  # pages documents: pull child pages
        ch = requests.get(f"{B}/search", headers=H, params={"filter:properties.document": eid, "filter:collection_id": cid, "limit": 200}).json()
        text = "\n".join("\n".join(c["properties"].get("bodyText", []) or c["properties"].get("indexText", [])) for c in ch.get("results", []))
    docs[eid] = dict(name=name, schema=full.get("schema"), chars=len(text))
    safe = name.replace("/", "__")
    open(f"{OUT}/hits_corpus/{safe}.{eid[:8]}.txt", "w").write(f"[OpenAleph entity {eid} schema={full.get('schema')} file={name}]\n{text}")
json.dump(dict(collection_id=cid, uploaded=up, ingest_wall_seconds=ingest_s, final_status=st, entity_schemas=schemas, total_entities=ents.get("total"),
               queries=qlog, exported_docs=docs), open(f"{OUT}/meta.json", "w"), indent=1)
print("schemas", schemas, "hits", len(hits), "exported chars", sum(d["chars"] for d in docs.values()))
