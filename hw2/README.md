## Производительность индексов
Для запросов вида 
```sql
WHERE first_name LIKE 'abc%' AND second_name LIKE 'abc%'
```
выбран **B-Tree** индекс с байтовым сравнением строк **text_pattern_ops**. Такие запросы, это диапазонное условие 
`'abc' <= value < 'abd'`, а это как раз структура, которая умеет искать диапазоны.

### Тестирование на чтение
Нагрузка осуществляется утилитой **k6** генерацией запросов на апи **/user/search** 
со случайными значениями имен от 2 до 5 символов из файла **tests/search.data**

Запуск приложения
```sh
docker compose up
```

Генерация и вставка тестовых данных
```sh
./db/generate_data.sh
```

Результаты нагрузочного тестирования без индекса сохраняются в **tests/read/**  
1 запрос в секунду
```sh
docker run --rm -e VUS=1 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js --summary-export=read/summary1.json
```
10 запросов в секунду
```sh
docker run --rm -e VUS=10 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js --summary-export=read/summary10.json
```
100 запросов в секунду
```sh
docker run --rm -e VUS=100 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js --summary-export=read/summary100.json
```
1000 запросов в секунду
```sh
docker run --rm -e VUS=1000 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js --summary-export=read/summary1000.json
```

Создание индексов
```sh
./db/create_index.sh
```
 
Результаты нагрузочного тестирования с индексом сохраняются в **tests/read_idx/**  
1 запрос в секунду
```sh
docker run --rm -e VUS=1 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js --summary-export=read_idx/summary1.json
```
10 запросов в секунду
```sh
docker run --rm -e VUS=10 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js --summary-export=read_idx/summary10.json
```
100 запросов в секунду
```sh
docker run --rm -e VUS=100 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js --summary-export=read_idx/summary100.json
```
1000 запросов в секунду
```sh
docker run --rm -e VUS=1000 -v "$PWD/tests:/tests" -w /tests grafana/k6 run search.js --summary-export=read_idx/summary1000.json
```

Остановка приложения
```sh
docker compose down
```

### Результат тестирования
|                             | 1  | 10 | 100  | 1000  |
|-----------------------------|----|----|------|-------|
| Задержка, ms                |    |    |      |       |
| Без индекса                 | 58 | 89 | 3000 | 44000 |
| С индексом                  | 22 | 39 | 49   | 4800  |
| Пропускная способность, rps |    |    |      |       |
| Без индекса                 | 1  | 10 | 23   | 21    |
| С индексом                  | 1  | 10 | 94   | 165   |

```
Задержка (ms)
 50000 |
 40000 |                       ✳
 30000 |
 20000 |
 10000 |
  9000 |
  8000 |
  7000 |
  6000 |
  5000 |                       ●
  4000 |
  3000 |                 ✳
  2000 |
  1000 |
   900 |
   800 |
   700 |
   600 |
   500 |
   400 |
   300 |
   200 |
   100 |
    90 |           ✳
    80 |
    70 |
    60 |     ✳
    50 |                 ●
    40 |           ●
    30 |
    20 |     ●
    10 |
       +-----+-----+-----+-----+-----
             1     10    100   1000 
 ✳ — Без индекса
 ● — С индексом
```

```
Пропускная способность (rps)
 170 |
 160 |                       ●
 150 |
 140 |
 130 |
 120 |
 110 |
 100 |
  90 |                 ●
  80 |
  70 |
  60 |
  50 |
  40 |
  30 |
  20 |                 ✳     ✳
  10 |          ✳●
   1 |    ✳●
     +-----+-----+-----+-----+-----
           1     10    100   1000 
 ✳ — Без индекса
 ● — С индексом    
```

План запроса без индекса
```
 Gather  (cost=1000.00..58266.35 rows=1 width=147)
   Workers Planned: 2
   ->  Parallel Seq Scan on users  (cost=0.00..57266.25 rows=1 width=147)
         Filter: (((first_name)::text ~~ 'Abc%'::text) AND ((second_name)::text ~~ 'Def%'::text))
```

План запроса с индексом  
```
 Index Scan using users_first_second_idx on users  (cost=0.43..8.46 rows=1 width=147)
   Index Cond: (((first_name)::text ~>=~ 'Abc'::text) AND ((first_name)::text ~<~ 'Abd'::text) AND ((second_name)::text ~>=~ 'Def'::text) AND ((second_name)::text ~<~ 'Deg'::text))
   Filter: (((first_name)::text ~~ 'Abc%'::text) AND ((second_name)::text ~~ 'Def%'::text))
```