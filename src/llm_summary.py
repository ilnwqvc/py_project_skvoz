import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_mart() -> pd.DataFrame:
    path = Path("data/mart/mart.csv")
    if not path.exists():
        raise FileNotFoundError(f"Не найден mart: {path}")
    df = pd.read_csv(path, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def load_dq_report() -> dict:
    path = Path("data/dq_report.json")
    if not path.exists():
        return {"summary": {"overall_status": "UNKNOWN", "counts": {"PASS": 0, "WARNING": 0, "FAIL": 0}}}
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_float(value: float) -> str:
    return f"{value:.2f}"


def build_context(cfg: dict, mart: pd.DataFrame, dq_report: dict) -> dict:
    rows = len(mart)
    last_row = mart.iloc[-1]
    prev_row = mart.iloc[-2] if len(mart) > 1 else mart.iloc[-1]
    top_precip = mart.nlargest(3, "P_sum")[["date", "P_sum"]].copy()
    top_precip["date"] = top_precip["date"].dt.strftime("%Y-%m-%d")
    top_precip["P_sum"] = top_precip["P_sum"].map(fmt_float)

    warmest = mart.loc[mart["T_mean"].idxmax()]
    coldest = mart.loc[mart["T_mean"].idxmin()]
    rainiest = mart.loc[mart["P_sum"].idxmax()]

    context = {
        "dataset_identity": {
            "variant_id": str(cfg["variant_id"]),
            "source": cfg["source_type"],
            "city_id": cfg["entity"]["city_id"],
            "city_name": cfg["entity"]["city_name"],
            "period_start": mart["date"].min().strftime("%Y-%m-%d"),
            "period_end": mart["date"].max().strftime("%Y-%m-%d"),
        },
        "schema_hints": {
            "mart_grain": "1 строка = 1 день по 1 городу",
            "table_name": "mart_variant_06",
            "row_count": str(rows),
        },
        "computed_metrics": {
            "t_mean_avg": fmt_float(mart["T_mean"].mean()),
            "t_mean_min": fmt_float(mart["T_mean"].min()),
            "t_mean_min_date": coldest["date"].strftime("%Y-%m-%d"),
            "t_mean_max": fmt_float(mart["T_mean"].max()),
            "t_mean_max_date": warmest["date"].strftime("%Y-%m-%d"),
            "p_sum_total": fmt_float(mart["P_sum"].sum()),
            "p_sum_max": fmt_float(mart["P_sum"].max()),
            "p_sum_max_date": rainiest["date"].strftime("%Y-%m-%d"),
            "wind_max_max": fmt_float(mart["wind_max"].max()),
            "rainy_hours_total": str(int(mart["rainy_hours"].sum())),
            "last_date": last_row["date"].strftime("%Y-%m-%d"),
            "last_t_mean": fmt_float(last_row["T_mean"]),
            "prev_date": prev_row["date"].strftime("%Y-%m-%d"),
            "prev_t_mean": fmt_float(prev_row["T_mean"]),
            "last_vs_prev_t_mean_diff": fmt_float(last_row["T_mean"] - prev_row["T_mean"]),
            "top_precip_days": top_precip.to_dict(orient="records"),
        },
        "quality_status": {
            "overall_status": dq_report["summary"]["overall_status"],
            "pass_count": str(dq_report["summary"]["counts"]["PASS"]),
            "warning_count": str(dq_report["summary"]["counts"]["WARNING"]),
            "fail_count": str(dq_report["summary"]["counts"]["FAIL"]),
        },
        "constraints": [
            "Не придумывать числа.",
            "Использовать только переданные метрики.",
            "Если данных не хватает, прямо написать об этом.",
            "Не считать новые метрики внутри ответа.",
        ],
    }
    return context


def build_prompt(context: dict) -> str:
    return (
        "Сделай короткую markdown-сводку на русском языке.\n"
        "Нужно 4 коротких пункта:\n"
        "- период и объем данных\n"
        "- температура\n"
        "- осадки\n"
        "- статус качества данных\n\n"
        "Используй только цифры и даты из контекста.\n"
        "Не придумывай числа.\n"
        "Не считай новые метрики.\n"
        "Если данных не хватает, так и скажи.\n\n"
        f"Контекст:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def extract_text_from_response(payload: dict) -> str:
    choice = payload["choices"][0]["message"]["content"]
    if isinstance(choice, str):
        return choice
    if isinstance(choice, list):
        parts = []
        for item in choice:
            text = item.get("text") or item.get("content") or ""
            if text:
                parts.append(text)
        return "\n".join(parts).strip()
    return ""


def call_llm(prompt: str, model: str, api_key: str) -> str:
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "Ты помощник-аналитик. Не выдумывай числа."},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    return extract_text_from_response(response.json())


def collect_allowed_tokens(value) -> set[str]:
    tokens = set()
    if isinstance(value, dict):
        for item in value.values():
            tokens.update(collect_allowed_tokens(item))
    elif isinstance(value, list):
        for item in value:
            tokens.update(collect_allowed_tokens(item))
    elif isinstance(value, str):
        tokens.add(value)
        tokens.update(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", value))
        tokens.update(re.findall(r"\b\d+(?:\.\d+)?\b", value))
    return tokens


def verify_summary(summary: str, context: dict) -> tuple[bool, list[str]]:
    allowed = collect_allowed_tokens(context)
    found = re.findall(r"\b\d{4}-\d{2}-\d{2}\b|\b\d+(?:\.\d+)?\b", summary)
    bad = [token for token in found if token not in allowed]
    return len(bad) == 0, bad


def local_summary(context: dict) -> str:
    c = context
    m = c["computed_metrics"]
    q = c["quality_status"]
    d = c["dataset_identity"]
    top_day = m["top_precip_days"][0]

    return (
        "# Сводка по mart\n\n"
        "_Сводка собрана локально из уже посчитанных агрегатов. Внешний API не вызывался, "
        "если ключ не задан или ответ не прошел проверку чисел._\n\n"
        f"- Период данных: {d['period_start']} - {d['period_end']}. В mart сейчас {c['schema_hints']['row_count']} строк.\n"
        f"- Средняя дневная температура по всему периоду: {m['t_mean_avg']}. Минимум {m['t_mean_min']} был {m['t_mean_min_date']}, максимум {m['t_mean_max']} был {m['t_mean_max_date']}.\n"
        f"- Сумма осадков за период: {m['p_sum_total']}. Самый дождливый день: {top_day['date']} с {top_day['P_sum']}.\n"
        f"- DQ статус: {q['overall_status']}. PASS={q['pass_count']}, WARNING={q['warning_count']}, FAIL={q['fail_count']}.\n"
    )


def append_log(log_path: Path, entry: dict) -> None:
    if not log_path.exists() or not log_path.read_text(encoding="utf-8").strip():
        header = "| timestamp_utc | mode | model | verification | notes |\n|---|---|---|---|---|\n"
        log_path.write_text(header, encoding="utf-8")

    line = (
        f"| {entry['timestamp_utc']} | {entry['mode']} | {entry['model']} | "
        f"{entry['verification']} | {entry['notes']} |\n"
    )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = load_config(args.config)
    mart = load_mart()
    dq_report = load_dq_report()

    docs_dir = Path("docs/llm")
    docs_dir.mkdir(parents=True, exist_ok=True)
    context_path = docs_dir / "context.json"
    summary_path = docs_dir / "summary.md"
    log_path = Path("docs/LLM_Usage_Log.md")

    context = build_context(cfg, mart, dq_report)
    prompt = build_prompt(context)
    context_path.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"

    mode = "local_summary"
    verification = "not_needed"
    notes = "API key is not set"
    summary = local_summary(context)

    if api_key:
        try:
            llm_text = call_llm(prompt, model, api_key)
            ok, bad_tokens = verify_summary(llm_text, context)
            if ok:
                mode = "llm_verified"
                verification = "passed"
                notes = "all numeric tokens matched context"
                summary = "# Сводка по mart\n\n" + llm_text.strip() + "\n"
            else:
                mode = "local_summary_after_check_failed"
                verification = "failed"
                notes = f"unexpected tokens: {', '.join(bad_tokens[:10])}"
        except Exception as e:
            mode = "local_summary_after_api_error"
            verification = "failed"
            notes = str(e).replace("|", "/")

    summary_path.write_text(summary, encoding="utf-8")

    append_log(
        log_path,
        {
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "model": model,
            "verification": verification,
            "notes": notes,
        },
    )

    print(f"context saved: {context_path}")
    print(f"summary saved: {summary_path}")
    print(f"log updated: {log_path}")
    print(f"mode: {mode}")
    print(f"verification: {verification}")


if __name__ == "__main__":
    main()
