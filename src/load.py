import os
from pathlib import Path

import pandas as pd
import yaml
from sqlalchemy import create_engine


def load_db_config():
    with open("configs/db.yml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)["db"]

    overrides = {
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "database": os.getenv("DB_NAME"),
    }
    for key, value in overrides.items():
        if value:
            cfg[key] = value

    return cfg


def get_engine(cfg):
    url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    return create_engine(url)


def load_to_db():
    path = Path("data/mart/mart.csv")
    if not path.exists():
        print("Нет mart файла")
        return 0

    df = pd.read_csv(path)
    cfg = load_db_config()
    engine = get_engine(cfg)

    with engine.begin() as conn:
        df.to_sql("mart_variant_06", conn, if_exists="replace", index=False)

    print(f"db host: {cfg['host']}:{cfg['port']}")
    print("table loaded: mart_variant_06")
    print(f"loaded rows to postgres: {len(df)}")
    return len(df)
