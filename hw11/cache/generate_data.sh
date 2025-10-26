#!/bin/bash
set -e

echo "Генерация данных постов..."
docker compose exec -T app python3 - posts < cache/generate_data.py > cache/posts.txt

echo "Загрузка данных постов в кэш..."
docker compose exec -T redis sh -c 'redis-cli < /dev/stdin > /dev/null' < cache/posts.txt

echo "Генерация данных пользователей..."
docker compose exec -T app python3 - users < cache/generate_data.py > cache/users.txt

echo "Загрузка данных пользователей в кэш..."
docker compose exec -T redis sh -c 'redis-cli < /dev/stdin > /dev/null' < cache/users.txt

echo "Генерация данных ленты..."
docker compose exec -T app python3 - feeds < cache/generate_data.py > cache/feeds.txt

echo "Загрузка данных ленты в кэш..."
docker compose exec -T redis sh -c 'redis-cli < /dev/stdin > /dev/null' < cache/feeds.txt

echo "Удаление файлов"
rm cache/posts.txt
rm cache/users.txt
rm cache/feeds.txt

echo "Загрузка завершена успешно"