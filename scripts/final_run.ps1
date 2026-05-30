$ErrorActionPreference = "Stop"

Write-Host "1/3 Поднимаю Docker-сервисы..."
docker compose up -d

Write-Host "2/3 Запускаю ETL-пайплайн..."
.\.venv\Scripts\python.exe src/pipeline.py --config configs/variant_06.yml --mode full

Write-Host "3/3 Строю сводку по mart..."
.\.venv\Scripts\python.exe src/llm_summary.py --config configs/variant_06.yml

Write-Host "Готово."
