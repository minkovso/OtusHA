#!/bin/bash
set -e

docker run --rm -e VUS=100 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js