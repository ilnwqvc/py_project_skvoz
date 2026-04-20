import argparse
from pathlib import Path
import json
from datetime import datetime

from extract import run_extract, load_config
from transform import transform_data, save_normalized, build_mart, save_mart
from dq import run_dq
from load import load_to_db


def load_state(path: Path):
    if not path.exists():
        return {"last_watermark": None, "last_run": None}
    return json.loads(path.read_text())


def save_state(path: Path, state: dict):
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=["full", "incremental"], required=True)

    args = parser.parse_args()

    cfg = load_config(args.config)
    state_path = Path(cfg["storage"]["state_path"])

    state = load_state(state_path)

    data, new_watermark = run_extract(cfg, args.mode)

    df = transform_data(data, cfg)
    save_normalized(df, cfg, args.mode)

    full_df = df
    if args.mode == "incremental":
        import pandas as pd
        full_df = pd.read_csv("data/normalized/normalized.csv", parse_dates=["ts"])

    mart = build_mart(full_df)
    save_mart(mart, cfg)

    dq_report = run_dq(args.config, layers=["normalized", "mart"])
    if dq_report["summary"]["overall_status"] == "FAIL":
        raise ValueError("DQ checks failed. Load stopped.")

    load_to_db()

    if new_watermark:
        state["last_watermark"] = new_watermark
        state["last_run"] = datetime.now().isoformat()
        save_state(state_path, state)

    print("PIPELINE DONE")


if __name__ == "__main__":
    main()
