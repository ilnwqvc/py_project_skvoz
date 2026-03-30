import pandas as pd
import yaml
from sqlalchemy import create_engine
from pathlib import Path


def load_config():
    with open("configs/db.yml", "r") as f:
        return yaml.safe_load(f)["db"]


def get_engine(cfg):
    url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    return create_engine(url)


def load_mart():
    path = Path(r"D:\progscode_2semestr\python_programming\data\mart\variant_06")
    files = sorted(path.glob("mart_daily_*.csv"))

    if not files:
        print("Нет mart файлов")
        return

    file = files[-1]
    print("Файл:", file)

    df = pd.read_csv(file)

    print("shape:", df.shape)
    print("columns:", df.columns.tolist())

    cfg = load_config()
    engine = get_engine(cfg)

    with engine.begin() as conn:
        df.to_sql("mart_variant_06", conn, if_exists="replace", index=False)

    print("Загрузка завершена")


if __name__ == "__main__":
    load_mart()