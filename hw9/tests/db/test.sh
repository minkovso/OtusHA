#!/bin/bash
set -e

./tests/stats.sh >> tests/db/stat.log &
docker run --rm -e VUS=100 -v "$PWD/tests:/tests" -w /tests grafana/k6 run --out json=db/metrics.json search.js &
wait