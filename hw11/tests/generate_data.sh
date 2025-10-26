#!/bin/bash
set -e

echo "Генерация тестовых данных ..."
docker compose exec -T app python3 - 1000 < tests/generate_data.py > tests/search.data

echo "Тестовые данные готовы"