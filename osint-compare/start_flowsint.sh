#!/usr/bin/env bash
# Starts Flowsint (prod images) with host networking (box docker has no iptables/bridge). Secrets from ~/.secrets/flowsint-local.env.
set -euo pipefail
set -a; . ~/.secrets/flowsint-local.env; set +a
D="sudo docker"
$D rm -f fs-pg fs-redis fs-neo4j fs-api >/dev/null 2>&1 || true
$D run -d --name fs-pg --network host -e POSTGRES_USER=flowsint -e POSTGRES_PASSWORD=flowsint -e POSTGRES_DB=flowsint postgres:15-alpine -c port=5433
$D run -d --name fs-redis --network host redis:7-alpine
$D run -d --name fs-neo4j --network host -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD -e 'NEO4J_PLUGINS=["apoc"]' -e NEO4J_server_memory_heap_max__size=1G neo4j:5
until $D exec fs-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" >/dev/null 2>&1; do sleep 3; done
# ~/.secrets/flowsint-api.env holds DATABASE_URL, NEO4J_*, AUTH_SECRET, MASTER_VAULT_KEY_V1, REDIS_URL, LLM_PROVIDER=openai (sudo strips env, so pass a file)
$D run -d --name fs-api --network host --env-file ~/.secrets/flowsint-api.env ghcr.io/reconurge/flowsint-api:latest
until curl -sf http://127.0.0.1:5001/health >/dev/null; do sleep 3; done; echo flowsint-api-up
