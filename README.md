# Weather ETL Project

Небольшой учебный проект по погодным данным Токио.  
В проекте есть:
- ETL-пайплайн
- DQ-проверки
- BI через Metabase
- Airflow DAG
- простой ML-блок
- LLM-сводка по агрегатам из `mart`

## Что в итоге получается

Основные артефакты:
- `data/raw/` — raw JSON
- `data/normalized/normalized.csv`
- `data/mart/mart.csv`
- `data/dq_report.json`
- `docs/dq_report.md`
- `docs/bi/`
- `docs/ml/`
- `docs/llm/summary.md`

## Быстрый запуск

Если нужен финальный прогон проекта, из корня:

```powershell
.\scripts\final_run.ps1
```

Этот скрипт:
1. поднимает Docker-сервисы
2. запускает ETL-пайплайн
3. строит LLM-сводку

## Если запускать руками

### 1. Установить зависимости

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Поднять сервисы

```powershell
docker compose up -d
docker compose ps
```

После этого должно быть доступно:
- Postgres: `localhost:5432`
- Metabase: `http://localhost:3000`
- Airflow: `http://localhost:8080`

### 3. Прогнать ETL

```powershell
.\.venv\Scripts\python.exe src/pipeline.py --config configs/variant_06.yml --mode full
```

### 4. Построить LLM-сводку

```powershell
.\.venv\Scripts\python.exe src/llm_summary.py --config configs/variant_06.yml
```

## BI

BI сделан через Metabase.  
Источник графиков — таблица `mart_variant_06` в Postgres.

Материалы лежат в:
- `docs/bi/`

## DQ

DQ-проверки запускаются отдельным модулем и встраиваются в пайплайн.

Основные файлы:
- `src/dq.py`
- `data/dq_report.json`
- `docs/dq_report.md`

## Airflow

DAG:
- `airflow/dags/etl_variant_06.py`

Порядок задач:
- `extract -> transform -> load -> dq`

Скрины:
- `docs/airflow/`

## ML

Для week13 сделан простой сценарий A:
- классификация дождливого часа
- baseline + LogisticRegression

Файлы:
- `notebooks/week13_ml.ipynb`
- `docs/ml/`

## LLM

LLM-шаг сделан отдельно, не внутри середины пайплайна.

Файлы:
- `src/llm_summary.py`
- `docs/llm/summary.md`
- `docs/LLM_Usage_Log.md`

Важно:
- в LLM передаются только агрегаты
- модель не должна считать числа сама
- цифры в summary проверяются кодом

## Переменные окружения

Для LLM используется переменная:
- `OPENAI_API_KEY`

В репозиторий ключ не кладется.  
Есть шаблон:
- `.env.example`

