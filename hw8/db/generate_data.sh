#!/bin/bash
set -e

echo "Генерация данных пользователей..."
docker compose exec -T app python3 - users 1000 < db/generate_data.py > db/users.csv

echo "Загрузка данных пользователей в базу..."
docker compose exec -e PGPASSWORD=postgres -T pgpool psql -U postgres -d prod -h localhost \
  -c "COPY prod.users (user_id, first_name, second_name, birthdate, city, biography)
      FROM STDIN WITH (FORMAT CSV)" < db/users.csv

echo "Генерация данных друзей..."
docker compose exec -T app python3 - friends 1000 < db/generate_data.py > db/friends.csv

echo "Загрузка данных друзей в базу..."
docker compose exec -e PGPASSWORD=postgres -T pgpool psql -U postgres -d prod -h localhost \
  -c "COPY prod.friends (user_id, friend_id)
      FROM STDIN WITH (FORMAT CSV)" < db/friends.csv

echo "Генерация данных постов..."
docker compose exec -T app python3 - posts 10000 < db/generate_data.py > db/posts.csv

echo "Загрузка данных постов в базу..."
docker compose exec -e PGPASSWORD=postgres -T pgpool psql -U postgres -d prod -h localhost \
  -c "COPY prod.posts (post_id, user_id, text, updated_at)
      FROM STDIN WITH (FORMAT CSV)" < db/posts.csv

echo "Генерация и загрузка диалогов в базу..."
docker compose exec -T app python3 - dialogs 10000 < db/generate_data.py

echo "Удаление файлов"
rm db/users.csv
rm db/friends.csv
rm db/posts.csv

echo "Загрузка завершена успешно"