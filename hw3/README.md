## Репликация
В качестве базы данных выбрана **bitnami/postgresql-repmgr**, которая может автоматически выбирать мастера 
и подписывать к нему реплики. В качестве балансировщика запросов выбрана **pgpool**, которая распределяет запросы по базам 
и отслеживает их состояние.

###  Тестирование на чтение без репликации
Нагрузка осуществляется утилитой **k6** генерацией запросов на апи **/user/search** 
со случайными значениями имен от 2 до 5 символов из файла **tests/search.data**

Запуск приложения
```sh
docker compose -f docker-compose.yml up
```

Генерация тестовых данных
```python
python3 db/generate_data.py 1000000 db/users.csv
```

Вставка данных в базу
```sh
docker compose exec -T db psql -U postgres -d prod \
  -c "COPY prod.users (id, first_name, second_name, birthdate, city, biography)
      FROM STDIN WITH (FORMAT CSV)" < db/users.csv
```

Статистика потребляемых ресурсов сохраняется в **tests/read/stat.log**  
Результат нагрузочного тестирования сохраняется в **tests/read/summary.json**
```sh
./tests/read/test.sh
```

Остановка приложения
```sh
docker compose -f docker-compose.yml down
```

###  Тестирование на чтение с репликацией
Нагрузка осуществляется утилитой **k6** генерацией запросов на апи **/user/search** 
со случайными значениями имен от 2 до 5 символов из файла **tests/search.data**

Запуск приложения
```sh
docker compose -f docker-compose-repl.yml up
```

Генерация тестовых данных
```python
python3 db/generate_data.py 1000000 db/users.csv
```

Вставка данных в базу
```sh
docker compose exec -e PGPASSWORD=postgres -T pgpool psql -U postgres -d prod -h localhost \
  -c "COPY prod.users (id, first_name, second_name, birthdate, city, biography)
      FROM STDIN WITH (FORMAT CSV)" < db/users.csv
```

Статистика потребляемых ресурсов сохраняется в **tests/read_repl/stat.log**  
Результат нагрузочного тестирования сохраняется в **tests/read_repl/summary.json**
```sh
./tests/read_repl/test.sh
```

Остановка приложения
```sh
docker compose -f docker-compose-repl.yml down
```

###  Тестирование на вставку с синхронной репликацией
Нагрузка осуществляется утилитой **k6** генерацией запросов на апи **/register** 
со случайными анкетами пользователей из файла **tests/register.data** с остановкой мастер-ноды

Запуск приложения
```sh
docker compose -f docker-compose-repl-sync.yml up
```

Результат тестирования сохраняется в **tests/write_repl_sync/summary.json**
```sh
./tests/write_repl_sync/test.sh
```

Проверка количества анкет
```sh
docker compose exec -e PGPASSWORD=postgres -T pgpool psql -U postgres -d prod -h localhost \
  -c "select count(*) from prod.users"
```

Остановка приложения
```sh
docker compose -f docker-compose-repl-sync.yml down
```

### Результат тестирования
|                             | Задержка, ms | Пропускная способность, rps |
|-----------------------------|--------------|-----------------------------|
| Без репликации              | 1160         | 45                          |
| С репликацией               | 1193         | 44                          |

|                    | max mem, % | max cpu, % |
|--------------------|------------|------------|
| Без репликации     |            |            |
| app                | 0.8        | 52         |
| db                 | 3.49       | 773        |
| С репликацией      |            |            |
| app                | 0.83       | 63         |
| pgpool             | 3.05       | 102        |
| postgres-replica-1 | 3.27       | 290        |
| postgres-replica-2 | 3.25       | 249        |
| postgres-primary-1 | 3.38       | 232        |

| Записано | Получено |
|----------|----------|
| 2613     | 2613     |