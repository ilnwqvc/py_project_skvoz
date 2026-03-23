import os
import sys
import yaml
import json
import requests
from datetime import datetime
from pathlib import Path


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_request_params(cfg: dict) -> dict:
    params = cfg["api"]["params"].copy()
    params["start_date"] = cfg["api"]["date_params"]["start_date"]
    params["end_date"] = cfg["api"]["date_params"]["end_date"]

    # hourly должен быть строкой через запятую
    if isinstance(params["hourly"], list):
        params["hourly"] = ",".join(params["hourly"])

    return params


def extract_data(cfg: dict) -> dict:
    url = cfg["api"]["base_url"]
    timeout = cfg["api"].get("timeout_sec", 30)
    params = build_request_params(cfg)

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("Ошибка: таймаут запроса")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"HTTP ошибка: {e}")
        sys.exit(1)


def save_raw(data: dict, cfg: dict):
    raw_path = Path(cfg["storage"]["raw_path"])
    city_id = cfg["entity"]["city_id"]

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = raw_path / city_id
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / f"{city_id}_{now_str}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Raw файл сохранён: {file_path}")


def main():
    config_path = "configs/variant_06.yml"
    cfg = load_config(config_path)

    data = extract_data(cfg)
    save_raw(data, cfg)


if __name__ == "__main__":
    main()