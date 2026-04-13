import pandas as pd
from sqlalchemy import create_engine
import yaml
from pathlib import Path


def load_db_config():
    with open("configs/db.yml", "r") as f:
        return yaml.safe_load(f)["db"]


def get_engine(cfg):
    url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    return create_engine(url)


def load_to_db():
    path = Path("data/mart/mart.csv")

    if not path.exists():
        print("Нет mart файла")
        return

    df = pd.read_csv(path)

    cfg = load_db_config()
    engine = get_engine(cfg)

    with engine.begin() as conn:
        df.to_sql("mart_variant_06", conn, if_exists="replace", index=False)

    print("Данные загружены в БД")