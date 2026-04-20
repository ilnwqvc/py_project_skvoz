# DQ Report

- Overall status: **PASS**
- PASS: 17
- FAIL: 0
- WARNING: 0

## Layer: normalized

- normalized_not_empty: PASS (FAIL)
  Причина: Таблица не пустая
  Детали: {"row_count": 696}
- normalized_not_null_keys: PASS (FAIL)
  Причина: NULL в критичных полях не найден
  Детали: {"columns": ["ts", "city_id"]}
- normalized_unique_business_key: PASS (FAIL)
  Причина: Бизнес-ключ уникален
  Детали: {"columns": ["city_id", "ts"]}
- normalized_ts_is_datetime: PASS (FAIL)
  Причина: Колонка корректно преобразуется в datetime
  Детали: {"column": "ts"}
- normalized_ts_monotonic: PASS (WARNING)
  Причина: Значения идут в монотонно возрастающем порядке
  Детали: {"column": "ts"}
- normalized_temperature_range: PASS (FAIL)
  Причина: Значения попадают в допустимый диапазон
  Детали: {"column": "temperature_2m"}
- normalized_humidity_range: PASS (FAIL)
  Причина: Значения попадают в допустимый диапазон
  Детали: {"column": "relative_humidity_2m"}
- normalized_precipitation_non_negative: PASS (FAIL)
  Причина: Значения попадают в допустимый диапазон
  Детали: {"column": "precipitation"}
- normalized_city_allowed: PASS (WARNING)
  Причина: Недопустимых значений не найдено
  Детали: {"column": "city_id", "allowed": ["JP_TYO"]}

## Layer: mart

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
- mart_precipitation_non_negative: PASS (FAIL)
  Причина: Значения попадают в допустимый диапазон
  Детали: {"column": "P_sum"}
- mart_rainy_hours_range: PASS (WARNING)
  Причина: Значения попадают в допустимый диапазон
  Детали: {"column": "rainy_hours"}
- mart_wind_non_negative: PASS (WARNING)
  Причина: Значения попадают в допустимый диапазон
  Детали: {"column": "wind_max"}
- mart_city_allowed: PASS (WARNING)
  Причина: Недопустимых значений не найдено
  Детали: {"column": "city_id", "allowed": ["JP_TYO"]}
