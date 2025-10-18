## Масштабируемая подсистема диалогов
В качестве базы данных для кеширования выбран **Couchbase**.  
Схема данных в couchbase `dialog_id:message_id (from, to, text, created_at)`.  
Шардирование осуществляется по ключу **dialog_id:message_id**, 
где **dialog_id** это сочетание отправителя и получателя, а **message_id** это ulid.  
Такая схема данных позволяет очень эффективно находить диалог между двумя пользователями.

Запуск приложения
```sh
docker compose up
```

Генерация и вставка данных в postgresql
```sh
./db/generate_data.sh
```

Генерация и вставка данных в redis 
```sh
./cache/generate_data.sh
```

Остановка приложения
```sh
docker compose down
```

### Решардинг
Решардинг в couchbase осуществляется без даунтайма, так как в текущем приложении используются key-value операции.

#### Добавление узла
Для добавления нового узла необходимо предварительно развернуть образ **couchbase:community** и
отправить запрос вида `couchbase-cli server-add`, либо воспользоваться графическим интерфейсом. 
После добавления узла нужно запустить решардинг post запросом на `/controller/rebalance`, 
либо воспользоваться графическим интерфейсом. Примеры команд есть в файле docker-compose сервиса init-cluster.

#### Удаление узла
Для удаления узла достаточно отправить post запрос вида
```sh
curl -u username:password -X POST \
  http://host:port/controller/rebalance \
  -d 'knownNodes=ns_1@node1,ns_1@node2' \
  -d 'ejectedNodes=ns_1@node3'
```
где **knownNodes** оставляемые узлы, **ejectedNodes** удаляемые узлы.  
Так же можно воспользоваться графическим интерфейсом.