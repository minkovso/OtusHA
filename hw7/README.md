## Применение In-Memory СУБД
В качестве базы для диалогов изначально была выбрана **Couchbase**, которая хорошо масштабируется, 
кеширует данные, имеет гибкий интерфейс и sql-подобный синтаксис. Было изменено обращение к данным 
с Key-Value API на N1QL, где можно реализовывать собственные функции обработки данных. В данном задании будет 
произведен нагрузочный тест между бакетами **couchbase** и **ephemeral** запросами на роут **/dialog/{friend_id}/list**.

#### couchbase
Данные хранятся в памяти и на диске, поддерживает репликацию, индексирование, N1QL-запросы, Key-Value API.

в init_cluster.sh
```sh
couchbase-cli bucket-create -c cb1.local -u admin -p password \
  --bucket prod \
  --bucket-type couchbase \
  --storage-backend couchstore \
  --bucket-ramsize 128 \
  --bucket-replica 2 > /dev/null
```

Запуск приложения
```sh
docker compose up
```

Генерация и вставка данных в postgresql и couchbase
```sh
./db/generate_data.sh
```

Генерация и вставка данных в redis 
```sh
./cache/generate_data.sh
```

Генерация данных для нагрузочного тестирования
```sh
./tests/generate_data.sh
```

Запуск нагрузочного тестирование, результат сохраняется в `./tests/persist/summary.json`
```sh
./tests/persist/test.sh
```

Остановка приложения
```sh
docker compose down
```

#### ephemeral
Данные хранятся только в памяти, поддерживает репликацию, индексирование, N1QL-запросы.

в init_cluster.sh
```sh
couchbase-cli bucket-create -c cb1.local -u admin -p password \
  --bucket prod \
  --bucket-type ephemeral \
  --bucket-ramsize 128 \
  --bucket-replica 2 > /dev/null
```

Запуск приложения
```sh
docker compose up
```

Генерация и вставка данных в postgresql и couchbase
```sh
./db/generate_data.sh
```

Генерация и вставка данных в redis 
```sh
./cache/generate_data.sh
```

Генерация данных для нагрузочного тестирования
```sh
./tests/generate_data.sh
```

Запуск нагрузочного тестирование, результат сохраняется в `./tests/memory/summary.json`
```sh
./tests/memory/test.sh
```

Остановка приложения
```sh
docker compose down
```

#### Результат тестирования
|                    | Задержка, ms | Пропускная способность, rps |
|--------------------|--------------|-----------------------------|
| couchbase          | 1230         | 43                          |
| ephemeral          | 1439         | 40                          |

Результаты получились примерно одинаковые, так как объем данных в бакете с типом couchbase, вероятно, 
полностью поместился в память во время вставки данных. В любом случае документация утверждает, что тип ephemeral 
является полноценным In-Memory СУБД. Тем не менее я оставляю в проекте тип couchbase, так как он имеет 
персистентность после перезапуска. Переход на N1QL-запросы так же добавили возможность гибко обращаться к данным и
писать собственные функции, к примеру get_messages(user_id) в init_cluster.sh.