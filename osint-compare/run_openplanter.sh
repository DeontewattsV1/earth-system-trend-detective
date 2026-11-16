#!/usr/bin/env bash
# Runs OpenPlanter's CLI LLM agent headlessly over the shared inputs. Key comes from env only.
set -euo pipefail
cd "$(dirname "$0")"
: "${OPENAI_API_KEY:?load keys: set -a; . ~/.secrets/openai.env}"
WS=${OP_OUT:-runs/openplanter}/ws; mkdir -p "$(dirname "$WS")"; rm -rf "$WS"; cp -r inputs "$WS"
. venvs/openplanter/bin/activate
# OpenPlanter auto-persists env keys to ~/.openplanter/credentials.json; remove it after the run
trap 'rm -f ~/.openplanter/credentials.json' EXIT
start=$(date +%s)
OPENPLANTER_MAX_DEPTH=2 timeout 1500 openplanter-agent --provider openai --model "${OP_MODEL:-gpt-4.1-mini}" \
  --workspace "$WS" --headless --reasoning-effort none --max-steps 40 --timeout 60 --task "$(cat TASK.txt)" \
  > ${OP_OUT:-runs/openplanter}/stdout.log 2> ${OP_OUT:-runs/openplanter}/stderr.log || echo "exit=$?" >> ${OP_OUT:-runs/openplanter}/stderr.log
echo "wall_seconds=$(( $(date +%s) - start ))" > ${OP_OUT:-runs/openplanter}/timing.txt
