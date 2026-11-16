#!/usr/bin/env bash
# Minimal OpenAleph stack (postgres, elasticsearch, api, worker, ingest-file) with host networking; reuses the redis started for Flowsint (db 1).
set -euo pipefail
D="sudo docker"; E=~/.secrets/openaleph.env
sudo mkdir -p /srv/aleph-data && sudo chmod 777 /srv/aleph-data
$D rm -f oa-pg oa-es oa-api oa-worker oa-ingest >/dev/null 2>&1 || true
$D run -d --name oa-pg --network host -e POSTGRES_USER=aleph -e POSTGRES_PASSWORD=aleph -e POSTGRES_DB=aleph postgres:17
$D run -d --name oa-es --network host -e ES_JAVA_OPTS="-Xms1g -Xmx1g" -e discovery.type=single-node -e xpack.security.enabled=false -e network.host=127.0.0.1 ghcr.io/openaleph/elasticsearch:latest
until curl -sf 127.0.0.1:9200/_cluster/health >/dev/null; do sleep 3; done
until $D exec oa-pg pg_isready -U aleph >/dev/null 2>&1; do sleep 2; done; sleep 3
$D run --rm --network host --env-file $E -v /srv/aleph-data:/data ghcr.io/openaleph/openaleph:latest aleph upgrade
$D run -d --name oa-api --network host --env-file $E -v /srv/aleph-data:/data ghcr.io/openaleph/openaleph:latest gunicorn --config /aleph/gunicorn.conf.py --workers 2 --bind 127.0.0.1:8000 --log-file -
$D run -d --name oa-worker --network host --env-file $E -v /srv/aleph-data:/data ghcr.io/openaleph/openaleph:latest procrastinate worker -q openaleph,openaleph-management
$D run -d --name oa-ingest --network host --env-file $E -v /srv/aleph-data:/data --tmpfs /tmp ghcr.io/openaleph/ingest-file:latest procrastinate worker -q ingest --concurrency 2
until curl -sf 127.0.0.1:8000/api/2/metadata >/dev/null; do sleep 3; done; echo openaleph-api-up
