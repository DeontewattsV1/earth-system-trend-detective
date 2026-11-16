"""GPT Researcher on the shared task. mode=local uses DOC_PATH=inputs/ (wiki md + ledger.md/csv + json); mode=web uses web search.
Keys come from env (OPENAI_API_KEY). Usage: python run_gptr.py local|web|aleph [doc_dir]"""
import asyncio, json, os, sys, time
mode = sys.argv[1]
out = f"runs/gptr_{mode}"
os.makedirs(out, exist_ok=True)
os.environ.setdefault("FAST_LLM", "openai:gpt-4.1-mini")
os.environ.setdefault("SMART_LLM", "openai:gpt-4.1-mini")
os.environ.setdefault("STRATEGIC_LLM", "openai:gpt-4.1-mini")
os.environ.setdefault("EMBEDDING", "openai:text-embedding-3-small")
if mode in ("local", "aleph"):
    os.environ["DOC_PATH"] = sys.argv[2] if len(sys.argv) > 2 else "runs/gptr_local/docs"
if mode == "web":
    os.environ.setdefault("RETRIEVER", "duckduckgo")
from gpt_researcher import GPTResearcher
task = open("TASK.txt").read().strip()
async def main():
    t = time.time()
    if mode == "web":
        q = task.replace("Use only the provided documents (wiki/ pages, ledger.csv / ledger.md, results.json, evidence_graph.json).", "") + \
            " Context: NASA POWER MERRA-2 regional monthly trends 1981-2025 for Svalbard, Central Sahel, Southern Amazon, California Central Valley, Delhi, Murray-Darling Basin, San Francisco Bay, cross-checked against GISTEMP v4 and GPCP v2.3."
        r = GPTResearcher(query=q, report_type="research_report", report_source="web")
    else:
        r = GPTResearcher(query=task, report_type="research_report", report_source="local")
    await r.conduct_research()
    report = await r.write_report()
    meta = dict(mode=mode, wall_seconds=round(time.time() - t, 1), costs_usd=r.get_costs(),
                sources=[s if isinstance(s, str) else str(s)[:300] for s in r.get_source_urls()],
                models={k: os.environ[k] for k in ("FAST_LLM", "SMART_LLM", "STRATEGIC_LLM", "EMBEDDING")})
    open(f"{out}/report.md", "w").write(report)
    json.dump(meta, open(f"{out}/meta.json", "w"), indent=1)
    print(json.dumps(meta, indent=1))
asyncio.run(main())
