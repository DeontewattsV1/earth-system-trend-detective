# Suggested updates for the ETD repo and the Space Apps form (not applied)

Nothing here has been pushed or edited in `/workspace/spaceapps-etd`. Apply it by hand if you approve.

## (a) Replacement for README lines 62–63

Current text:
```
- OpenPlanter is used for its wiki format and graph parser; its LLM agent (needs API keys) was not run.
  The OSINT tool comparison (OpenPlanter vs Flowsint vs GPT Researcher–OpenAleph) is proposed, not done.
```

Replacement:
```
- OpenPlanter provides the wiki format and graph parser (37/37 intended edges recovered, 0 decoy edges). Its LLM agent
  was also run (gpt-4.1-mini) on a fixed question over the same wiki and ledger, together with Flowsint (graph import +
  AI chat) and GPT Researcher, both alone and on top of a local OpenAleph ingest/search stack. Every numeric claim was
  checked against results.json (see osint-compare/REPORT.md). Two findings: (1) as shipped, every tool silently truncated
  its input. OpenPlanter invented numbers for rows it never read (9 wrong claims), and Flowsint and GPT Researcher covered
  only 4 and 1 of the 8 robust trends. (2) With one setting (OPENPLANTER_MAX_OBS_CHARS=60000), OpenPlanter named all 8
  robust trends and the Delhi contradiction with 1 minor numeric error. This is a single-run tool comparison, not a
  scientific result. The evidence ledger remains the source of truth.
```

## (b) Paragraph for the Space Apps "Detailed Project Description" (118 words)

> We also tested whether AI investigation tools can faithfully summarise our evidence ledger. OpenPlanter's agent, Flowsint, and GPT Researcher (alone and with an OpenAleph search index) each answered the same question over the same wiki and 72-row ledger. A script then checked every numeric claim against results.json. Run as shipped, each tool silently truncated its input. One invented numbers for rows it never read, and the others missed most of the eight robust trends. With one setting changed, OpenPlanter listed all eight robust trends and the Delhi contradiction, with a single minor error. The lesson matches our design: an AI summary is only trustworthy when it is checked against the evidence ledger. The full comparison costs under US$0.30.

## (c) Files to add to the repo under `osint-compare/`

Include these. They contain no keys; I scanned them for OpenAI key patterns and got 0 hits.
- `REPORT.md`, `SUBMISSION_UPDATE.md` (optional), `TASK.txt`
- Scripts: `make_ledger_csv.py`, `run_all.sh`, `run_openplanter.sh`, `run_gptr.py`, `start_openaleph.sh`, `run_openaleph_ingest.py`, `start_flowsint.sh`, `run_flowsint.py`, `score.py`
- `scoring/scores.json`, `scoring/*.claims.json`
- Answers:
  - `runs/openplanter/answer.md`, `runs/openplanter_obs60k/answer.md`
  - `runs/gptr_local/report.md`, `runs/gptr_aleph/report.md`, `runs/gptr_web/report.md`
  - `runs/flowsint/answer_A_select_all.md`, `runs/flowsint/answer_B_select_non_unverified.md`
- Run metadata:
  - `runs/openplanter/stdout.log`, `runs/openplanter_obs60k/stdout.log` (agent traces; no keys)
  - `runs/gptr_*/meta.json`, `runs/openaleph/meta.json`
  - `runs/flowsint/meta.json`, `runs/flowsint/import_graph.json`

Do not add:
- `inputs/` (duplicates repo data)
- `runs/*/ws/` (workspace copies plus OpenPlanter session dumps)
- `runs/gptr_local/docs/`, `runs/openaleph/hits_corpus/` (copies of inputs)
- `runs/*/stderr.log`, `runs/gptr_*/stdout.log` (verbose; no keys, but noisy)
- `runs/flowsint/stream_*.txt`, `runs/flowsint/graph_readback.json` (internal ids)
- `logs/`, `src/`, `venvs/`
- Anything in `~/.secrets/`
