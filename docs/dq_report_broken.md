# DQ-отчет

- Итоговый статус: **FAIL**
- PASS: 12
- FAIL: 4
- WARNING: 3

## Слой: normalized

- normalized_expected_columns: PASS (FAIL)
  Причина: Список колонок совпадает с контрактом
  Детали: {"columns": ["ts", "temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "city_id"]}
- normalized_not_empty: PASS (FAIL)
  Причина: Таблица не пустая
  Детали: {"row_count": 697}
- normalized_not_null_keys: FAIL (FAIL)
  Причина: Найдены NULL в критичных полях
  Детали: {"null_counts": {"city_id": 1}}
- normalized_unique_business_key: FAIL (FAIL)
  Причина: Найдены дубли по бизнес-ключу
  Детали: {"columns": ["city_id", "ts"], "duplicate_rows": 2, "sample": [{"city_id": "JP_TYO", "ts": "2026-02-01 01:00:00"}, {"city_id": "JP_TYO", "ts": "2026-02-01 01:00:00"}]}
- normalized_ts_is_datetime: PASS (FAIL)
  Причина: Колонка корректно преобразуется в datetime
  Детали: {"column": "ts"}
- normalized_ts_monotonic: WARNING (WARNING)
  Причина: Нарушен монотонный порядок
  Детали: {"column": "ts", "group_by": ["city_id"], "invalid_groups": ["('JP_TYO',)"]}
- normalized_temperature_range: PASS (FAIL)
  Причина: Значения попадают в допустимый диапазон
  Детали: {"column": "temperature_2m"}
- normalized_humidity_range: PASS (FAIL)
  Причина: Значения попадают в допустимый диапазон
  Детали: {"column": "relative_humidity_2m"}
- normalized_precipitation_non_negative: FAIL (FAIL)
  Причина: Есть значения вне диапазона
  Детали: {"column": "precipitation", "invalid_rows": 1, "sample": [{"precipitation": -5.0}], "min": 0}
- normalized_city_allowed: WARNING (WARNING)
  Причина: Есть значения вне допустимого списка
  Детали: {"column": "city_id", "allowed": ["JP_TYO"], "invalid_rows": 1, "sample": [{"city_id": NaN}]}

## Слой: mart

- mart_expected_columns: PASS (FAIL)
  Причина: Список колонок совпадает с контрактом
  Детали: {"columns": ["date", "city_id", "T_mean", "P_sum", "wind_max", "rainy_hours"]}
- mart_not_empty: PASS (FAIL)
  Причина: Таблица не пустая
  Детали: {"row_count": 29}
- mart_not_null_keys: PASS (FAIL)
  Причина: NULL в критичных полях не найден
  Детали: {"columns": ["date", "city_id"]}
- mart_unique_business_key: PASS (FAIL)
  Причина: Бизнес-ключ уникален
  Детали: {"columns": ["date", "city_id"]}
- mart_date_is_datetime: PASS (FAIL)
  Причина: Колонка корректно преобразуется в datetime
  Детали: {"column": "date"}
- mart_precipitation_non_negative: FAIL (FAIL)
  Причина: Есть значения вне диапазона
  Детали: {"column": "P_sum", "invalid_rows": 1, "sample": [{"P_sum": -1.0}], "min": 0}
- mart_rainy_hours_range: WARNING (WARNING)
  Причина: Есть значения вне диапазона
  Детали: {"column": "rainy_hours", "invalid_rows": 1, "sample": [{"rainy_hours": 30}], "min": 0, "max": 24}
- mart_wind_non_negative: PASS (WARNING)
  Причина: Значения попадают в допустимый диапазон
  Детали: {"column": "wind_max"}
- mart_city_allowed: PASS (WARNING)
  Причина: Недопустимых значений не найдено
  Детали: {"column": "city_id", "allowed": ["JP_TYO"]}
