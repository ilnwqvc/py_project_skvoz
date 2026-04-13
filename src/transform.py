import pandas as pd
from pathlib import Path


def transform_data(data: dict, cfg: dict) -> pd.DataFrame:
    hourly = data["hourly"]

    df = pd.DataFrame({
        "ts": hourly["time"],
        "temperature_2m": hourly["temperature_2m"],
        "relative_humidity_2m": hourly["relative_humidity_2m"],
        "precipitation": hourly["precipitation"],
        "wind_speed_10m": hourly["wind_speed_10m"],
    })

    df["city_id"] = cfg["entity"]["city_id"]

    df["ts"] = pd.to_datetime(df["ts"])

    cols = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"]
    df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")

    df = df[
        (df["temperature_2m"].between(-80, 60)) &
        (df["relative_humidity_2m"].between(0, 100)) &
        (df["precipitation"] >= 0)
    ]

    df = df.dropna(subset=["ts"])

    df = df.drop_duplicates(subset=["city_id", "ts"])

    return df


def save_normalized(df: pd.DataFrame, cfg: dict, mode: str):
    path = Path("data/normalized/normalized.csv")
    path.parent.mkdir(parents=True, exist_ok=True)

    if mode == "full" or not path.exists():
        df.to_csv(path, index=False)
    else:
        old = pd.read_csv(path, parse_dates=["ts"])
        df = pd.concat([old, df])
        df = df.drop_duplicates(subset=["city_id", "ts"])
        df.to_csv(path, index=False)

    print("NORMALIZED обновлен")


def build_mart(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = df["ts"].dt.date

    mart = df.groupby(["date", "city_id"], as_index=False).agg(
        T_mean=("temperature_2m", "mean"),
        P_sum=("precipitation", "sum"),
        wind_max=("wind_speed_10m", "max"),
        rainy_hours=("precipitation", lambda x: (x > 0).sum())
    )

    return mart


def save_mart(df: pd.DataFrame, cfg: dict):
    path = Path("data/mart/mart.csv")
    path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(path, index=False)
    print("MART обновлен")