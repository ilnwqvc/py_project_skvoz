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