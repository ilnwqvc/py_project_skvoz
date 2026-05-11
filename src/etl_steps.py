import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from dq import run_dq
from extract import load_config, run_extract
from load import load_to_db
from transform import build_mart, save_mart, save_normalized, transform_data


def load_latest_raw(cfg: dict) -> tuple[dict, Path]:
    city_id = cfg["entity"]["city_id"]
    raw_dir = Path(cfg["storage"]["raw_path"]) / city_id
    candidates = sorted(raw_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"В raw не найдено файлов: {raw_dir}")

    latest = candidates[0]
    with open(latest, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data, latest


def save_state(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def step_extract(config_path: str, mode: str) -> None:
    cfg = load_config(config_path)
    data, new_watermark, raw_path = run_extract(cfg, mode)
    hourly_rows = len(data.get("hourly", {}).get("time", []))

    print(f"config used: {config_path}")
    print(f"hourly rows from api: {hourly_rows}")
    print(f"raw file ready: {raw_path}")

    if new_watermark:
        state_path = Path(cfg["storage"]["state_path"])
        state = {"last_watermark": new_watermark, "last_run": datetime.now().isoformat()}
        save_state(state_path, state)
        print(f"state updated: {state_path}")


def step_transform(config_path: str, mode: str) -> None:
    cfg = load_config(config_path)
    raw_data, raw_path = load_latest_raw(cfg)

    df = transform_data(raw_data, cfg)
    save_normalized(df, cfg, mode)

    full_df = df.copy()
    if mode == "incremental":
        full_df = pd.read_csv("data/normalized/normalized.csv", parse_dates=["ts"])
    elif "ts" in full_df.columns and full_df["ts"].dtype == object:
        full_df["ts"] = pd.to_datetime(full_df["ts"])

    mart = build_mart(full_df.copy())
    save_mart(mart, cfg)

    print(f"config used: {config_path}")
    print(f"raw source: {raw_path}")
    print(f"normalized rows: {len(df)}")
    print(f"mart rows: {len(mart)}")
    print("saved files: data/normalized/normalized.csv, data/mart/mart.csv")


def step_load(config_path: str) -> None:
    _cfg = load_config(config_path)
    loaded_rows = load_to_db()
    print(f"config used: {config_path}")
    print(f"loaded rows to postgres: {loaded_rows}")


def step_dq(config_path: str) -> None:
    report = run_dq(config_path, layers=["normalized", "mart"])
    counts = report["summary"]["counts"]
    print(f"config used: {config_path}")
    print(f"dq checks: PASS={counts['PASS']} WARNING={counts['WARNING']} FAIL={counts['FAIL']}")
    print("dq files: data/dq_report.json, docs/dq_report.md")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["extract", "transform", "load", "dq"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    args = parser.parse_args()

    if args.step == "extract":
        step_extract(args.config, args.mode)
    elif args.step == "transform":
        step_transform(args.config, args.mode)
    elif args.step == "load":
        step_load(args.config)
    elif args.step == "dq":
        step_dq(args.config)


if __name__ == "__main__":
    main()
