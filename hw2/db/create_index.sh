#!/bin/bash
set -e

echo "Создание индекса..."
docker compose exec -T db psql -U postgres -d prod \
  -c "CREATE INDEX users_first_second_idx
          ON prod.users (first_name text_pattern_ops, second_name text_pattern_ops)"

echo "Сбор статистики..."
docker compose exec -T db psql -U postgres -d prod \
  -c "ANALYZE prod.users"

echo "Индекс создан успешно"