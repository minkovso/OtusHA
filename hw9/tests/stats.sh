#!/bin/bash
set -e

SECONDS=0
while (( SECONDS < 120 )); do
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}\t{{.BlockIO}}\t{{.NetIO}}"
  sleep 10
done