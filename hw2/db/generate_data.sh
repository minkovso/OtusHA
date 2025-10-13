#!/bin/bash
set -e

echo "Генерация данных..."
python3 db/generate_data.py 1000000 db/data.csv

echo "Загрузка данных в базу..."
docker compose exec -T db psql -U postgres -d prod \
  -c "COPY prod.users (id, first_name, second_name, birthdate, city, biography)
      FROM STDIN WITH (FORMAT CSV)" < db/data.csv

echo "Сбор статистики..."
docker compose exec -T db psql -U postgres -d prod \
  -c "ANALYZE prod.users"

echo "Загрузка завершена успешно"