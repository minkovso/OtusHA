#!/bin/bash
set -e

./tests/stats.sh >> tests/persist/stat.log &
docker run --rm -e VUS=100 -v "$PWD/tests:/tests" -w /tests grafana/k6 run dialog.js --summary-export=persist/summary.json &
wait