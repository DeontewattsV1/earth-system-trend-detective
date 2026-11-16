#!/usr/bin/env bash
# Reproduce the OSINT tool comparison end to end. Keys are read from env files only; nothing is printed.
#   ~/.secrets/openai.env          OPENAI_API_KEY=...
#   ~/.secrets/flowsint-local.env  AUTH_SECRET, MASTER_VAULT_KEY_V1, NEO4J_PASSWORD, FS_USER_PW (random, local only)
#   ~/.secrets/flowsint-api.env    env-file for the Flowsint API container (see start_flowsint.sh)
#   ~/.secrets/openaleph.env       env-file for OpenAleph containers; ~/.secrets/openaleph-api.env ALEPH_API_KEY (from `aleph createuser --admin`)
# Prereqs: python3.12 + uv, docker (box used static docker 27.3.1, dockerd --iptables=false --bridge=none, host networking).
set -euo pipefail; cd "$(dirname "$0")"
set -a; . ~/.secrets/openai.env; set +a
# 0. tools (pinned to the commits recorded in REPORT.md)
[ -d src/OpenPlanter ] || git clone https://github.com/ShinMegamiBoson/OpenPlanter src/OpenPlanter
[ -d src/flowsint ] || git clone https://github.com/reconurge/flowsint src/flowsint
[ -d src/openaleph ] || git clone https://github.com/openaleph/openaleph src/openaleph
[ -d venvs/openplanter ] || { uv venv -p 3.12 venvs/openplanter; VIRTUAL_ENV=venvs/openplanter uv pip install -e src/OpenPlanter; }
[ -d venvs/gptr ] || { uv venv -p 3.12 venvs/gptr; VIRTUAL_ENV=venvs/gptr uv pip install gpt-researcher==0.17.0 ddgs requests; }
# 1. shared inputs (copied from the ETD repo, read-only)
mkdir -p inputs; cp -r ../spaceapps-etd/wiki inputs/; cp ../spaceapps-etd/data/results.json ../spaceapps-etd/data/evidence_graph.json inputs/
python3 make_ledger_csv.py
# 2. OpenPlanter: as shipped, then with a larger observation window
./run_openplanter.sh
OP_OUT=runs/openplanter_obs60k OPENPLANTER_MAX_OBS_CHARS=60000 ./run_openplanter.sh
# 3. GPT Researcher: local docs (flattened copy of inputs) and web
rm -rf runs/gptr_local/docs; mkdir -p runs/gptr_local/docs runs/gptr_web runs/gptr_aleph
for f in $(cd inputs && find wiki -name '*.md'); do cp inputs/$f runs/gptr_local/docs/$(echo $f | tr / _); done
cp inputs/ledger.md inputs/ledger.csv runs/gptr_local/docs/; cp inputs/results.json runs/gptr_local/docs/results.json.txt; cp inputs/evidence_graph.json runs/gptr_local/docs/evidence_graph.json.txt
venvs/gptr/bin/python run_gptr.py local > runs/gptr_local/stdout.log 2> runs/gptr_local/stderr.log
venvs/gptr/bin/python run_gptr.py web > runs/gptr_web/stdout.log 2> runs/gptr_web/stderr.log || true
# 4. GPT Researcher–OpenAleph: OpenAleph ingest + fixed queries -> hits corpus -> GPT Researcher synthesis
./start_openaleph.sh
( set -a; . ~/.secrets/openaleph-api.env; set +a; venvs/gptr/bin/python run_openaleph_ingest.py )
venvs/gptr/bin/python run_gptr.py aleph runs/openaleph/hits_corpus > runs/gptr_aleph/stdout.log 2> runs/gptr_aleph/stderr.log
# 5. Flowsint: stack, then patch the missing `openai` package into the API image (see REPORT.md), then import + AI chat
./start_flowsint.sh
rm -rf /tmp/oai; uv pip install --target /tmp/oai --python-platform x86_64-manylinux_2_28 --python-version 3.12 "openai>=2,<3"
SP=/app/.venv/lib/python3.12/site-packages; for p in /tmp/oai/*; do n=$(basename $p); sudo docker exec fs-api test -e $SP/$n || sudo docker cp $p fs-api:$SP/; done
( set -a; . ~/.secrets/flowsint-local.env; set +a; venvs/gptr/bin/python run_flowsint.py )
# 6. scoring (claim extraction with gpt-4.1-mini, deterministic checks against the ledger)
REEXTRACT=1 venvs/gptr/bin/python score.py
# 7. secret scan of everything this produced
! rg -l 'sk-(proj|svcacct)-' --glob '!src/**' --glob '!venvs/**' . && echo "no keys in outputs"
