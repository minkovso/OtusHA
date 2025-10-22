#!/bin/bash
set -e

if curl -u admin:password -fs http://cb1.local:8091/pools/default > /dev/null 2>&1; then
  echo "Couchbase уже настроен, пропуск инициализации"
  exit 0
fi;

couchbase-cli node-init -c cb1.local --node-init-hostname cb1.local > /dev/null

echo "Инициализация Couchbase..."
couchbase-cli cluster-init -c cb1.local \
  --cluster-username admin \
  --cluster-password password \
  --services query,index,data \
  --cluster-ramsize 256 > /dev/null
echo "Инициализация Couchbase прошла успешно"

echo "Добавление нод..."
couchbase-cli server-add -c cb1.local -u admin -p password \
  --server-add cb2.local \
  --server-add-username admin \
  --server-add-password password \
  --services query,index,data > /dev/null

couchbase-cli server-add -c cb1.local -u admin -p password \
  --server-add cb3.local \
  --server-add-username admin \
  --server-add-password password \
  --services query,index,data > /dev/null
echo "Ноды добавлены успешно"

echo "Решардинг..."
curl -fs -u admin:password -X POST http://cb1.local:8091/controller/rebalance \
  -d knownNodes=ns_1@cb1.local,ns_1@cb2.local,ns_1@cb3.local > /dev/null

until curl -s -u admin:password http://cb1.local:8091/pools/default | grep -q '"balanced":true'; do
  echo "Решардинг..."
  sleep 5
done;
echo "Решардинг завершен успешно"

echo "Создание бакета..."
couchbase-cli bucket-create -c cb1.local -u admin -p password \
  --bucket prod \
  --bucket-type couchbase \
  --storage-backend couchstore \
  --bucket-ramsize 128 \
  --bucket-replica 2 > /dev/null

echo "Бакет создан успешно"

echo "Создание коллекции..."
couchbase-cli collection-manage -c cb1.local -u admin -p password \
  --bucket prod \
  --create-scope prod > /dev/null

couchbase-cli collection-manage -c cb1.local -u admin -p password \
  --bucket prod \
  --create-collection prod.messages > /dev/null

sleep 2

curl -s -u admin:password -X POST http://cb1.local:8093/query/service \
  -d 'statement=CREATE INDEX messages_from ON prod.prod.messages(`from`)'
echo "Коллекция создана успешно"