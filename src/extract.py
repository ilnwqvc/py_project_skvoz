import json
import sys
from datetime import datetime
from pathlib import Path

import requests
import yaml


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state(state_path: Path) -> dict:
    if not state_path.exists():
        return {"last_watermark": None, "last_run": None}

    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state_path: Path, state: dict):
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def build_request_params(cfg: dict, mode: str, state: dict) -> dict:
    params = cfg["api"]["params"].copy()

    if mode == "full" or state["last_watermark"] is None:
        start_date = cfg["api"]["date_params"]["start_date"]
    else:
        start_date = state["last_watermark"]

    end_date = cfg["api"]["date_params"]["end_date"]

    params["start_date"] = start_date
    params["end_date"] = end_date

    if isinstance(params["hourly"], list):
        params["hourly"] = ",".join(params["hourly"])

    return params


def extract_data(cfg: dict, mode: str, state: dict) -> dict:
    url = cfg["api"]["base_url"]
    timeout = cfg["api"].get("timeout_sec", 30)
    params = build_request_params(cfg, mode, state)

    print(f"extract mode: {mode}")
    print(f"config source: {cfg['source_type']}")
    print(f"request period: {params['start_date']} -> {params['end_date']}")

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


def save_raw(data: dict, cfg: dict) -> Path:
    raw_path = Path(cfg["storage"]["raw_path"])
    city_id = cfg["entity"]["city_id"]

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = raw_path / city_id
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / f"{city_id}_{now_str}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"raw saved: {file_path} ({file_path.stat().st_size} bytes)")
    return file_path


def extract_new_watermark(data: dict) -> str | None:
    try:
        times = data["hourly"]["time"]
        return max(times)
    except Exception:
        return None


def run_extract(cfg: dict, mode: str):
    state_path = Path(cfg["storage"]["state_path"])
    state = load_state(state_path)

    data = extract_data(cfg, mode, state)
    raw_path = save_raw(data, cfg)
    new_watermark = extract_new_watermark(data)

    return data, new_watermark, raw_path


if __name__ == "__main__":
    print("Используй через pipeline.py")
