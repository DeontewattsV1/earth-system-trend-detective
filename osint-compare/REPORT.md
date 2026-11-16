# OSINT tool comparison on the Earth System Trend Detective evidence ledger

**OpenPlanter vs Flowsint vs GPT Researcher–OpenAleph**, run on the box on Sun 15 Nov 2026 between 8:13 and 8:40 PM PT.
This compares tools. It is not a scientific discovery and claims no novelty. The science lives in `results.json`. Here we only measure how faithfully each tool reports it.

## 1. Method

**Same task for every tool** (`TASK.txt`):
> Which regional Earth-system trends in this evidence ledger are robust (significant and corroborated by an independent NASA product), which are likely chance or artifacts, and what should a user check next? Use only the provided documents (wiki/ pages, ledger.csv / ledger.md, results.json, evidence_graph.json). For every numeric claim, cite the ledger row id (e.g. sahel:T2M) or wiki page it comes from. Keep the answer under 900 words.

**Same inputs for every tool** (`inputs/`, copied read-only from `/workspace/spaceapps-etd`):
- `wiki/`: the OpenPlanter-format evidence wiki (26 pages: index, 4 sources, 1 decoy, 20 findings)
- `results.json`: the full analysis, with 7 regions and a 72-row evidence ledger
- `evidence_graph.json`: the graph from OpenPlanter's `WikiGraphModel` parser (37 of 37 intended edges, precision 1.0, recall 1.0, 0 decoy edges)
- `ledger.csv` / `ledger.md`: a deterministic flattening of the 72 ledger rows (`make_ledger_csv.py`), so that tools that only read text see every row

Each tool reads these files in its own native way, as described in section 2.

**Ground truth.** The ledger has 72 rows: 8 `verified`, 1 `contradicted` (delhi:T2M) and 63 `unverified`. By primary verdict, 42 are significant, 11 suggestive and 19 not significant. The 8 robust rows are svalbard:T2M, sahel:T2M, sahel:PRECTOTCORR, amazon:T2M, amazon:PRECTOTCORR, california:T2M, murray:T2M and sfbay:T2M.

**Claim checking** (`score.py`, outputs in `scoring/`):
1. gpt-4.1-mini (temperature 0, JSON mode) breaks each answer into atomic claims: row id, field, value, and any asserted status.
2. Every claim is then checked deterministically against the ledger:
   - **Numbers** (slope, p, corroborating slope and p, anomaly correlation): correct if the sign matches and the value is within 2% (slopes) or within rounding (p-values).
   - **Statuses** (verified, contradicted, unverified, significant and so on): checked against `status`, `primary_verdict` and `corr_verdict`.
   - **"Chance/artifact" labels**: correct for contradicted or non-significant rows, and wrong for verified rows. They count as unverifiable for significant-but-uncorroborated rows, because the ledger makes no call on those.
   - **General statements** not tied to a row: unverifiable against results.json.
3. I read every answer and checked every `wrong` verdict by hand (all confirmed). I also counted robust-row coverage by hand, because the extractor sometimes skips status claims.

**Rubric.** Eight criteria, each scored 0–5, equal weights, for a total out of 40:

| Criterion | 5 = | 0–1 = |
|---|---|---|
| A. Factual accuracy | ≥98% of checkable claims correct | <70% |
| B. Hallucinated claims | 0 wrong claims (1–2 → 4, 3–5 → 2, >5 → 1) | many invented numbers or rows |
| C. Coverage of robust vs chance | 8/8 robust, 0 false-robust, Delhi contradiction and specific chance rows named | ≤1 robust row |
| D. Citation and traceability | row ids on every numeric claim | file-level or no citations |
| E. Setup effort and time | pip install, no patches | multi-container stack plus patches or glue |
| F. Run time | <30 s | >10 min |
| G. Cost | <$0.10 | >$2 |
| H. Graph/wiki usefulness | uses the wiki or graph structure natively | none |

## 2. What actually ran (per tool)

Commits: OpenPlanter `81d7562`, flowsint `64ac40d`, openaleph `904a554`. GPT Researcher is the PyPI release `gpt-researcher==0.17.0`; the repo HEAD `ddd4db3` was cloned only for reference.

Docker setup: apt was unavailable on the box (HTTP 500 from the mirror). Docker 27.3.1 ran from the static binaries with `dockerd --iptables=false --bridge=none`, so every container uses `--network host`.

### OpenPlanter: LLM agent run ✅
- **Install and run:** `pip install -e` the repo, then the CLI agent ran headless:
  `openplanter-agent --provider openai --model gpt-4.1-mini --reasoning-effort none --headless --max-steps 40 --task "$(cat TASK.txt)"`
  The workspace was a copy of `inputs/`. OpenPlanter seeded its runtime wiki (`.openplanter/wiki/`) from `wiki/` and read `index.md` first, as its prompt requires.
- **Fix needed:** the first attempt failed with HTTP 400 because OpenPlanter sends `reasoning_effort` to non-reasoning models, so `--reasoning-effort none` was added.
- **Run 1, as shipped:** 5 model calls, 13 s, 87,389 input and 1,552 output tokens. Its `read_file` output is capped by `max_observation_chars=6000`, so it saw only the first ~6 KB of each file (the Svalbard and Sahel rows). It still answered for all 7 regions, and the Delhi, Murray and SF Bay rows contain numbers it never saw.
- **Run 2, one setting changed** (`OPENPLANTER_MAX_OBS_CHARS=60000`): 8 calls, 34 s, 463,165 input and 3,888 output tokens. It wrote `regional_trends_summary.md` with row ids and CSV line numbers.
- **Outputs:** `runs/openplanter*/stdout.log` (full trace), `answer.md`, `ws/.openplanter/sessions/*/{events,replay}.jsonl`.
- **Security note:** OpenPlanter silently saved the env key to `~/.openplanter/credentials.json` (mode 600). I deleted that file, and `run_openplanter.sh` now removes it on exit.

### GPT Researcher (local docs mode) ✅, web mode ⚠️
- **Local mode:** `report_source="local"` with `DOC_PATH` set to a flattened copy of the same inputs (the JSON files were renamed `.txt` so the loader reads them). Models: gpt-4.1-mini for fast, smart and strategic, plus text-embedding-3-small. Run time 19.9 s, cost $0.0043 as reported by GPT Researcher.
- **What it saw:** its retrieval picked a few chunks, mostly the first ledger rows. The report covers only Svalbard.
- **Web mode:** ran with the DuckDuckGo retriever (needed `pip install ddgs`). It returned no sources from the box ("I could not gather any source material…"). Cost $0.0005, and it is not scored.
- **Outputs:** `runs/gptr_local/`, `runs/gptr_web/`.

### GPT Researcher–OpenAleph pipeline ✅ (minimal real OpenAleph stack)
- **OpenAleph stack:** a real local stack ran on the official images: postgres 17, `openaleph/elasticsearch`, the `openaleph` API (gunicorn), the `openaleph` procrastinate worker and `ingest-file`. The stack took 208 s to come up after ~80 s of image pulls. It used `aleph upgrade` and `aleph createuser --admin` (the API key went to `~/.secrets`).
- **Ingest:** all 30 input files went in through the ingest API (HTTP 201), and processing took 21 s. The result was 27 PlainText entities, 1 Table and 2 Documents.
  - The two `.json` files became Documents with **no extracted text**.
  - The CSV became a Table whose rows were not exported. `ledger.md` carries the full ledger, so nothing was lost.
- **Not run:** `ftm-analyze` (NER and entity extraction), `ftm-translate` and the UI. Their 30 queued analyze tasks stayed `todo`.
- **Search:** 10 fixed queries derived from the task (verified, contradicted, significant, "not significant", suggestive, unverified, GISTEMP, GPCP, corroborated, artifact OR chance) returned 28 unique hit documents (54,840 chars). Their text, tagged with OpenAleph entity ids, went to `runs/openaleph/hits_corpus/`.
- **Synthesis:** GPT Researcher ran in local mode over that corpus. Run time 18.3 s, cost $0.0049.
- **Outputs:** `runs/openaleph/meta.json` (queries, hits, schemas), `runs/gptr_aleph/report.md`.

### Flowsint ✅ (one image patch)
- **Stack:** the prod images (`flowsint-api:latest`, postgres 15, redis 7, neo4j 5) ran with host networking. The frontend container and the Celery enricher workers were not started. The AI chat was driven through the API exactly as the UI does.
- **Patch needed:** the published `flowsint-api:latest` image (6 weeks old) **lacks the `openai` package**, even though `flowsint-core/pyproject.toml` requires `openai>=2`. The chat returned HTTP 500 `ModuleNotFoundError: openai` until I copied `openai` 2.54.0 into the container's site-packages. Flowsint's OpenAI provider hardcodes **gpt-4o-mini**.
- **Graph import:** Flowsint's enrichers are for OSINT data (DNS, WHOIS, IP and so on) and cannot apply to climate data. The closest meaningful use was its graph plus AI chat. The 72 ledger rows were imported through the documented JSON import (`/import/analyze` then `/import/execute`): 82 nodes (72 findings as `Phrase` with id, status, slope, p and corroboration in the ≤100-char label; 7 regions; 3 products as `Organization`) and 158 edges (IN_REGION, MEASURED_BY, CORROBORATED_BY, CONTRADICTED_BY, COMPARED_WITH). The import took 8 s, with 0 errors.
- **Chat:** Flowsint's chat sends only the selected nodes' **labels** as context, and the server truncates that context to **2,000 chars**.
  - **Variant A (select all, the primary same-input run):** 82 labels, 4,025 chars, cut to 2,000 chars (about the Svalbard, Sahel, Amazon and part of the California rows). Took 19.7 s.
  - **Variant B (analyst pre-selects the 9 non-`unverified` nodes):** 637 chars. Took 16.8 s. This is not the same input; it is reported to show the ceiling.
- **OpenAI key:** stored through Flowsint's vault API, encrypted in its local Postgres.
- **Outputs:** `runs/flowsint/` (`import_graph.json`, `graph_readback.json`, `answer_*.md`, `stream_*.txt`, `meta.json` including the exact context the LLM saw).

## 3. Results

### Claim counts (automatic extraction, deterministic check; wrong verdicts hand-confirmed)

| Run | Claims | Correct | **Wrong** | Unverifiable | Numeric checked (wrong) | Row-id citations | Robust rows named (hand count) | False "robust" | Delhi contradiction |
|---|---|---|---|---|---|---|---|---|---|
| OpenPlanter, as shipped | 71 | 55 | **9** | 7 | 35 (7) | 30 | 8/8 | 2 (murray:PRECTOTCORR, sfbay:PRECTOTCORR) | yes |
| OpenPlanter, obs 60k | 27* | 25 | **1** | 1 | 21 (1) | 9 ids + CSV line nos. | **8/8** | 0 | yes |
| GPT Researcher, local | 16 | 11 | 0 | 5 | 9 (0) | 0 (file-level) | 1/8 | 0 | no |
| GPT Researcher–OpenAleph | 15 | 7 | 0 | 8 | 6 (0) | 0 (file-level) | 1/8 | 0 | no |
| Flowsint A, select all | 25 | 24 | 0 | 1 | 24 (0) | 9 | 4/8 | 0 | no |
| Flowsint B, pre-selected† | 43 | 40 | 0 | 3 | 32 (0) | 8 | 7/8 | 0 | yes |
| GPT Researcher, web | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no sources retrieved |

\* The extractor under-counted this answer. A full hand read found every row-level status correct, and the CSV line numbers it cites (e.g. svalbard:T2M row 2, delhi:T2M row 44) match `ledger.csv`.
† Not the same input: a human pre-filtered the graph.

**What the wrong claims were:**
- **OpenPlanter, as shipped:** all 9 fall on rows beyond its 6 KB view, so they are hallucinated.
  - delhi:RH2M is given as +0.933 %/dec (the ledger says +2.764; 0.933 is actually Sahel's value).
  - delhi:ALLSKY_SFC_SW_DWN is given as −0.199 (the ledger says −0.626; −0.199 is Sahel's).
  - Wrong slopes for murray:T2M (0.214 vs 0.2403), sfbay:T2M (0.254 vs 0.1721), murray:PRECTOTCORR, sfbay:PRECTOTCORR and murray:GWETROOT.
  - murray:PRECTOTCORR and sfbay:PRECTOTCORR are called "verified" when both are `unverified`.
- **OpenPlanter, obs 60k:** its one error is "p < 1e-10" for svalbard:T2M, which is actually 1.67e-10.

**What no tool did:** none raised the multiple-testing caveat ("72 tests at p < 0.05 means ~3–4 chance results"). That caveat is in the ETD README but not in the shared inputs, so no tool was penalised for it.

### Rubric scores (0–5 each; primary rows use as-shipped defaults and identical inputs)

| Run | A Acc. | B Halluc. | C Coverage | D Cite | E Setup | F Time | G Cost | H Graph/wiki | **Total /40** |
|---|---|---|---|---|---|---|---|---|---|
| OpenPlanter (as shipped) | 3 | 1 | 3 | 3 | 5 | 5 (13 s) | 5 ($0.037) | 4 | **29** |
| GPT Researcher (local) | 5 | 5 | 1 | 2 | 5 | 5 (20 s) | 5 ($0.004) | 1 | **29** |
| GPT Researcher–OpenAleph | 5 | 5 | 1 | 2 | 2 | 4 (≈40 s + 5 min stack) | 5 ($0.005) | 2 | **26** |
| Flowsint (A, select all) | 5 | 5 | 2 | 4 | 2 | 5 (28 s) | 5 (~$0.001 est.) | 3 | **31** |
| *OpenPlanter, obs 60k (one env var)* | 5 | 4 | 5 | 5 | 5 | 5 (34 s) | 4 ($0.19) | 4 | ***37*** |
| *Flowsint B (pre-selected)* | 5 | 5 | 4 | 4 | 2 | 5 | 5 | 3 | *33* |

**Why each tool scored as it did on H (graph/wiki):**
- **OpenPlanter (4):** consumes its own wiki format natively; the parser recovered 37/37 edges. Its agent read files rather than traversing links.
- **Flowsint (3):** builds a real Neo4j graph that can be explored visually, but its LLM sees only node labels, capped at 2,000 chars.
- **OpenAleph (2):** full-text index with entity ids, but no relation graph without ftm-analyze. JSON files are not indexed as text.
- **GPT Researcher (1):** no graph at all.

### Cost (OpenAI)

| Item | Model | Tokens in / out | USD |
|---|---|---|---|
| OpenPlanter, as shipped | gpt-4.1-mini | 87,389 / 1,552 | 0.0374 |
| OpenPlanter, obs 60k | gpt-4.1-mini | 463,165 / 3,888 | 0.1915 |
| OpenPlanter, first attempt (HTTP 400) | none | 0 / 0 | 0 |
| GPT Researcher, local | gpt-4.1-mini + emb-3-small | (tool-reported) | 0.0043 |
| GPT Researcher, web | same | (tool-reported) | 0.0005 |
| GPT Researcher–OpenAleph | same | (tool-reported) | 0.0049 |
| Flowsint chats A+B | gpt-4o-mini (hardcoded) | ~1.1k / ~2.0k (estimated from chars; Flowsint doesn't report usage) | ~0.0014 |
| Claim extraction for scoring | gpt-4.1-mini | 11,684 / 13,021 | 0.0255 |
| **Total** | | | **≈ $0.27** (budget $10) |

Prices assumed: gpt-4.1-mini $0.40/$1.60 per 1M tokens, gpt-4o-mini $0.15/$0.60 per 1M tokens. These are estimates from token counts; I did not check the OpenAI billing dashboard.

## 4. Verdict

- **With as-shipped defaults, no tool is reliable enough to stand in for the ledger.**
  - Flowsint (31) and GPT Researcher (29) made no false claims, but they covered only 4/8 and 1/8 of the robust trends.
  - OpenPlanter (29) covered all regions but **invented numbers for rows it never read** (9 wrong claims, 2 false "verified").
  - GPT Researcher–OpenAleph (26) was accurate, but retrieval-limited and the heaviest to stand up.
- **With one configuration change, OpenPlanter is the clear best fit for this project** (37/40): `OPENPLANTER_MAX_OBS_CHARS=60000`. It named all 8 robust trends with no false ones, flagged the Delhi contradiction, cited row ids and CSV line numbers, made 1 minor numeric error, and cost $0.19.
- **The lesson for ETD:** the risk is silent truncation, not the model.
  - OpenPlanter clips file reads at 6 KB.
  - Flowsint clips chat context at 2,000 chars.
  - GPT Researcher retrieves a handful of chunks.
  - In every case the evidence ledger, not the LLM narrative, should stay the source of truth, and any LLM summary should be machine-checked against it, as `score.py` does.

## 5. Limitations
- One run per tool. LLM output varies from run to run, and no repeat runs or confidence intervals were done.
- Models differ: Flowsint hardcodes gpt-4o-mini, and the others used gpt-4.1-mini.
- Claim extraction is itself done by an LLM. Every `wrong` verdict was hand-confirmed, but some claims were missed (notably for OpenPlanter obs 60k and Flowsint A status claims), which is why coverage was hand-counted.
- Rubric weights are equal and the scale points are a judgement call. The claim counts are the more objective numbers.
- Flowsint: the API image was patched (`openai` missing); the frontend and enrichers did not run; the "select all" UI behaviour was emulated through the API following `chat-prompt.tsx` `formatContext`.
- OpenAleph: ftm-analyze (NER), ftm-translate and the UI were not run; JSON inputs were not text-extracted; the query list was fixed by me, not chosen by an agent.
- GPT Researcher web mode returned no sources from the box (DuckDuckGo), so the web comparison is missing.
- All of this ran on one shared box with host-networked Docker. No timing was repeated.

## 6. Criteria check (brief items 1–7)
1. **OpenPlanter LLM agent run with the key over the wiki and graph on a fixed task, full output and logs saved:** **met** (two runs).
2. **GPT Researcher on the same task, local-docs mode, output saved:** **met.** Web mode was **attempted but produced nothing** (no sources).
3. **OpenAleph stood up locally (Docker), same docs ingested, paired with GPT Researcher:** **met, minimal stack.** Postgres, Elasticsearch, API, worker and ingest-file ran; ftm-analyze and UI did not.
4. **Flowsint installed (Docker), equivalent graph investigation with its LLM feature:** **met, with one image patch.** OSINT enrichers don't apply to this data and were not run.
5. **Same task and inputs, written rubric, every numeric claim checked, correct/wrong/unverifiable counts:** **met.** Numeric claims were checked automatically and the wrong ones hand-confirmed. Flowsint B is flagged as a different input.
6. **REPORT.md, raw outputs, reproducible run script reading keys from env:** **met** (`run_all.sh`; keys come only from `~/.secrets/*.env`).
7. **Re-read and unmet items listed:** done. Partially unmet: GPT Researcher web mode (no sources); OpenAleph analyze/NER stage; no repeat runs.

## 7. Suggested replacement for ETD README lines 62–63
See `SUBMISSION_UPDATE.md`.

## 8. Files
- `TASK.txt`, `inputs/`, `make_ledger_csv.py`
- `run_all.sh`, `run_openplanter.sh`, `run_gptr.py`, `start_openaleph.sh`, `run_openaleph_ingest.py`, `start_flowsint.sh`, `run_flowsint.py`, `score.py`
- `runs/openplanter/`, `runs/openplanter_obs60k/`, `runs/gptr_local/`, `runs/gptr_web/`, `runs/openaleph/`, `runs/gptr_aleph/`, `runs/flowsint/`
- `scoring/*.claims.json`, `scoring/scores.json`
- `logs/` (setup logs)
- `src/` (tool clones) and `venvs/` are not deliverables.
