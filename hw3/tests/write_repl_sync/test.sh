#!/bin/bash
set -e

docker run --rm -e VUS=100 -v "$PWD/tests:/tests" -w /tests grafana/k6 run register.js --summary-export=write_repl_sync/summary.json
docker compose -f docker-compose-repl-sync.yml stop postgresql-0