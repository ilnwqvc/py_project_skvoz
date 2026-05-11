import argparse
import json
import os
from pathlib import Path

import pandas as pd
import yaml


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_layer_data(layer: str) -> pd.DataFrame:
    layer_paths = {
        "normalized": Path("data/normalized/normalized.csv"),
        "mart": Path("data/mart/mart.csv"),
    }
    path = layer_paths[layer]
    if not path.exists():
        raise FileNotFoundError(f"Файл слоя {layer} не найден: {path}")
    return pd.read_csv(path)


def make_result(rule: dict, status: str, reason: str, details: dict | None = None) -> dict:
    return {
        "name": rule["name"],
        "type": rule["type"],
        "severity": rule["severity"],
        "status": status,
        "reason": reason,
        "details": details or {},
    }


def violation_status(rule: dict) -> str:
    return "WARNING" if rule["severity"] == "WARNING" else "FAIL"


def check_non_empty(df: pd.DataFrame, rule: dict) -> dict:
    if len(df) > 0:
        return make_result(rule, "PASS", "Таблица не пустая", {"row_count": int(len(df))})
    return make_result(rule, "FAIL", "Таблица пустая", {"row_count": 0})


def check_expected_columns(df: pd.DataFrame, rule: dict) -> dict:
    expected = list(rule["columns"])
    actual = list(df.columns)
    missing = [column for column in expected if column not in actual]
    extra = [column for column in actual if column not in expected]

    if not missing and not extra:
        return make_result(rule, "PASS", "Список колонок совпадает с контрактом", {"columns": expected})

    details = {"expected": expected, "actual": actual}
    if missing:
        details["missing_columns"] = missing
    if extra:
        details["extra_columns"] = extra
    return make_result(rule, violation_status(rule), "Схема DataFrame не совпадает с контрактом", details)


def check_not_null(df: pd.DataFrame, rule: dict) -> dict:
    columns = rule["columns"]
    null_counts = {column: int(df[column].isna().sum()) for column in columns}
    bad_columns = {column: count for column, count in null_counts.items() if count > 0}
    if not bad_columns:
        return make_result(rule, "PASS", "NULL в критичных полях не найден", {"columns": columns})
    return make_result(rule, violation_status(rule), "Найдены NULL в критичных полях", {"null_counts": bad_columns})


def check_unique_key(df: pd.DataFrame, rule: dict) -> dict:
    columns = rule["columns"]
    duplicates = df[df.duplicated(subset=columns, keep=False)]
    duplicate_count = int(len(duplicates))
    if duplicate_count == 0:
        return make_result(rule, "PASS", "Бизнес-ключ уникален", {"columns": columns})
    sample = duplicates[columns].head(5).astype(str).to_dict(orient="records")
    return make_result(
        rule,
        violation_status(rule),
        "Найдены дубли по бизнес-ключу",
        {"columns": columns, "duplicate_rows": duplicate_count, "sample": sample},
    )


def check_numeric_range(df: pd.DataFrame, rule: dict) -> dict:
    column = rule["column"]
    numeric = pd.to_numeric(df[column], errors="coerce")
    invalid_mask = numeric.isna()

    if "min" in rule:
        invalid_mask = invalid_mask | (numeric < rule["min"])
    if "max" in rule:
        invalid_mask = invalid_mask | (numeric > rule["max"])

    invalid_rows = df.loc[invalid_mask, [column]].head(5).to_dict(orient="records")
    invalid_count = int(invalid_mask.sum())
    if invalid_count == 0:
        return make_result(rule, "PASS", "Значения попадают в допустимый диапазон", {"column": column})

    details = {"column": column, "invalid_rows": invalid_count, "sample": invalid_rows}
    if "min" in rule:
        details["min"] = rule["min"]
    if "max" in rule:
        details["max"] = rule["max"]
    return make_result(rule, violation_status(rule), "Есть значения вне диапазона", details)


def check_convertible_datetime(df: pd.DataFrame, rule: dict) -> dict:
    column = rule["column"]
    converted = pd.to_datetime(df[column], errors="coerce")
    invalid_mask = converted.isna()
    invalid_count = int(invalid_mask.sum())
    if invalid_count == 0:
        return make_result(rule, "PASS", "Колонка корректно преобразуется в datetime", {"column": column})
    sample = df.loc[invalid_mask, [column]].head(5).astype(str).to_dict(orient="records")
    return make_result(
        rule,
        violation_status(rule),
        "Есть значения, которые не преобразуются в datetime",
        {"column": column, "invalid_rows": invalid_count, "sample": sample},
    )


def check_allowed_values(df: pd.DataFrame, rule: dict) -> dict:
    column = rule["column"]
    allowed = set(rule["values"])
    invalid = df[~df[column].isin(allowed)]
    invalid_count = int(len(invalid))
    if invalid_count == 0:
        return make_result(rule, "PASS", "Недопустимых значений не найдено", {"column": column, "allowed": sorted(allowed)})
    sample = invalid[[column]].drop_duplicates().head(5).astype(str).to_dict(orient="records")
    return make_result(
        rule,
        violation_status(rule),
        "Есть значения вне допустимого списка",
        {"column": column, "allowed": sorted(allowed), "invalid_rows": invalid_count, "sample": sample},
    )


def check_monotonic_increasing(df: pd.DataFrame, rule: dict) -> dict:
    column = rule["column"]
    group_by = rule.get("group_by", [])
    invalid_groups = []

    if group_by:
        for group_key, group_df in df.groupby(group_by, dropna=False):
            converted = pd.to_datetime(group_df[column], errors="coerce")
            if converted.isna().any() or not converted.is_monotonic_increasing:
                invalid_groups.append(str(group_key))
    else:
        converted = pd.to_datetime(df[column], errors="coerce")
        if converted.isna().any() or not converted.is_monotonic_increasing:
            invalid_groups.append("all_rows")

    if not invalid_groups:
        return make_result(rule, "PASS", "Значения идут в монотонно возрастающем порядке", {"column": column})
    return make_result(
        rule,
        violation_status(rule),
        "Нарушен монотонный порядок",
        {"column": column, "group_by": group_by, "invalid_groups": invalid_groups[:5]},
    )


CHECKS = {
    "expected_columns": check_expected_columns,
    "non_empty": check_non_empty,
    "not_null": check_not_null,
    "unique_key": check_unique_key,
    "numeric_range": check_numeric_range,
    "convertible_datetime": check_convertible_datetime,
    "allowed_values": check_allowed_values,
    "monotonic_increasing": check_monotonic_increasing,
}


def run_checks(df: pd.DataFrame, rules: list[dict]) -> list[dict]:
    results = []
    for rule in rules:
        checker = CHECKS[rule["type"]]
        results.append(checker(df.copy(), rule))
    return results


def summarize_results(layer_results: dict[str, list[dict]]) -> dict:
    all_results = [result for results in layer_results.values() for result in results]
    summary = {"PASS": 0, "FAIL": 0, "WARNING": 0}

    for result in all_results:
        summary[result["status"]] += 1

    overall_status = "FAIL" if summary["FAIL"] > 0 else "PASS"
    return {"overall_status": overall_status, "counts": summary}


def save_json_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    _safe_write_text(path, payload)


def save_markdown_report(report: dict, path: Path) -> None:
    lines = [
        "# DQ Report",
        "",
        f"- Overall status: **{report['summary']['overall_status']}**",
        f"- PASS: {report['summary']['counts']['PASS']}",
        f"- FAIL: {report['summary']['counts']['FAIL']}",
        f"- WARNING: {report['summary']['counts']['WARNING']}",
        "",
    ]

    for layer, results in report["layers"].items():
        lines.append(f"## Layer: {layer}")
        lines.append("")
        for result in results:
            lines.append(f"- {result['name']}: {result['status']} ({result['severity']})")
            lines.append(f"  Причина: {result['reason']}")
            if result["details"]:
                lines.append(f"  Детали: {json.dumps(result['details'], ensure_ascii=False)}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    _safe_write_text(path, "\n".join(lines))


def _safe_write_text(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    try:
        os.replace(tmp_path, path)
    except PermissionError:
        fallback = path.with_name(f"{path.stem}_latest{path.suffix}")
        tmp_path.replace(fallback)
        print(f"warning: report file was locked, saved fallback copy: {fallback}")


def inject_demo_issues(dataframes: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    broken = {layer: df.copy() for layer, df in dataframes.items()}

    if "normalized" in broken and not broken["normalized"].empty:
        normalized = broken["normalized"].copy()
        normalized.loc[0, "city_id"] = None
        normalized.loc[0, "precipitation"] = -5
        normalized = pd.concat([normalized, normalized.iloc[[1]]], ignore_index=True)
        broken["normalized"] = normalized

    if "mart" in broken and not broken["mart"].empty:
        mart = broken["mart"].copy()
        mart.loc[0, "P_sum"] = -1
        mart.loc[0, "rainy_hours"] = 30
        broken["mart"] = mart

    return broken


def build_report(cfg: dict, layers: list[str], demo_broken: bool = False) -> dict:
    layer_rules = cfg.get("dq_rules", {})
    dataframes = {layer: load_layer_data(layer) for layer in layers}

    if demo_broken:
        dataframes = inject_demo_issues(dataframes)

    layer_results = {}
    for layer in layers:
        rules = layer_rules.get(layer, [])
        layer_results[layer] = run_checks(dataframes[layer], rules)

    report = {
        "summary": summarize_results(layer_results),
        "layers": layer_results,
        "demo_broken": demo_broken,
    }
    return report


def print_report(report: dict) -> None:
    print("DQ SUMMARY")
    print("overall_status:", report["summary"]["overall_status"])
    print("PASS:", report["summary"]["counts"]["PASS"])
    print("FAIL:", report["summary"]["counts"]["FAIL"])
    print("WARNING:", report["summary"]["counts"]["WARNING"])
    print()

    for layer, results in report["layers"].items():
        print(f"[{layer}]")
        for result in results:
            print(f"- {result['name']}: {result['status']} ({result['severity']}) - {result['reason']}")
        print()


def run_dq(config_path: str, layers: list[str] | None = None, demo_broken: bool = False) -> dict:
    cfg = load_config(config_path)
    selected_layers = layers or list(cfg.get("dq_rules", {}).keys())
    report = build_report(cfg, selected_layers, demo_broken=demo_broken)

    suffix = "_broken" if demo_broken else ""
    json_path = Path(f"data/dq_report{suffix}.json")
    md_path = Path(f"docs/dq_report{suffix}.md")

    save_json_report(report, json_path)
    save_markdown_report(report, md_path)
    print_report(report)
    print(f"JSON report saved to: {json_path}")
    print(f"Markdown report saved to: {md_path}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--layers", nargs="*", choices=["normalized", "mart"])
    parser.add_argument("--demo-broken", action="store_true")
    args = parser.parse_args()

    run_dq(args.config, layers=args.layers, demo_broken=args.demo_broken)


if __name__ == "__main__":
    main()
