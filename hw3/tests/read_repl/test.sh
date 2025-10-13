#!/bin/bash
set -e

./tests/stats.sh >> tests/read_repl/stat.log &
docker run --rm -e VUS=100 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js --summary-export=read_repl/summary.json &
wait