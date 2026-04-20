## Normalized layer

Grain:
Одна строка = одно почасовое наблюдение погоды в Токио

| field                   | type      | nullable | description                          |
|------------------------|----------|----------|--------------------------------------|
| ts                     | timestamp | no       | Дата-время наблюдения                |
| temperature_2m         | float     | yes      | Температура (°C)                     |
| relative_humidity_2m   | float     | yes      | Влажность (%)                        |
| precipitation          | float     | yes      | Осадки (мм)                          |
| wind_speed_10m         | float     | yes      | Скорость ветра (м/с)                 |
| city_id                | string    | no       | Идентификатор города (JP_TYO)        |

## Mart layer

Grain:
Одна строка = один день по одному городу

| field       | type   | nullable | description                                |
|------------|--------|----------|--------------------------------------------|
| date       | date   | no       | Дата агрегирования                         |
| city_id    | string | no       | Идентификатор города                       |
| T_mean     | float  | yes      | Средняя температура за день                |
| P_sum      | float  | yes      | Сумма осадков за день                      |
| wind_max   | float  | yes      | Максимальная скорость ветра за день        |
| rainy_hours| int    | yes      | Количество часов с precipitation > 0       |

## DQ rules

DQ-проверки запускаются после `transform` для слоя `normalized` и после построения `mart`, до `load`.

### Normalized

| rule | check | severity | violation |
|------|-------|----------|-----------|
| normalized_not_empty | таблица не пустая | FAIL | в слое нет ни одной строки |
| normalized_not_null_keys | `ts`, `city_id` не NULL | FAIL | хотя бы одно из ключевых полей пустое |
| normalized_unique_business_key | уникальность `(city_id, ts)` | FAIL | найден дубль по бизнес-ключу |
| normalized_ts_is_datetime | `ts` приводится к datetime | FAIL | есть непарсимые значения |
| normalized_ts_monotonic | `ts` возрастает внутри `city_id` | WARNING | порядок времени нарушен |
| normalized_temperature_range | `temperature_2m` в диапазоне `[-80, 60]` | FAIL | значение ниже минимума или выше максимума |
| normalized_humidity_range | `relative_humidity_2m` в диапазоне `[0, 100]` | FAIL | влажность вне допустимого диапазона |
| normalized_precipitation_non_negative | `precipitation >= 0` | FAIL | осадки отрицательные |
| normalized_city_allowed | `city_id` входит в допустимый список | WARNING | встретился неожиданный город |

### Mart

| rule | check | severity | violation |
|------|-------|----------|-----------|
| mart_not_empty | таблица не пустая | FAIL | в витрине нет строк |
| mart_not_null_keys | `date`, `city_id` не NULL | FAIL | одно из ключевых полей пустое |
| mart_unique_business_key | уникальность `(date, city_id)` | FAIL | найден дубль по дню и городу |
| mart_date_is_datetime | `date` приводится к datetime | FAIL | дата не парсится |
| mart_precipitation_non_negative | `P_sum >= 0` | FAIL | сумма осадков отрицательная |
| mart_rainy_hours_range | `rainy_hours` в диапазоне `[0, 24]` | WARNING | число дождливых часов некорректно |
| mart_wind_non_negative | `wind_max >= 0` | WARNING | максимальная скорость ветра отрицательная |
| mart_city_allowed | `city_id` входит в допустимый список | WARNING | встретился неожиданный город |
