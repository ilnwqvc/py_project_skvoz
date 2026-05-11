from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/opt/airflow/project"
CONFIG_PATH = "configs/variant_06.yml"
COMMON_PREFIX = f"cd {PROJECT_DIR} && export PYTHONIOENCODING=UTF-8"


with DAG(
    dag_id="etl_variant_06",
    schedule="*/5 * * * *",
    start_date=datetime(2026, 5, 1),
    catchup=False,
    tags=["etl", "variant_06"],
) as dag:
    extract = BashOperator(
        task_id="extract",
        bash_command=(
            f"{COMMON_PREFIX} && "
            f"python src/etl_steps.py extract --config {CONFIG_PATH} --mode full"
        ),
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=(
            f"{COMMON_PREFIX} && "
            f"python src/etl_steps.py transform --config {CONFIG_PATH} --mode full"
        ),
    )

    load = BashOperator(
        task_id="load",
        bash_command=(
            f"{COMMON_PREFIX} && "
            f"python src/etl_steps.py load --config {CONFIG_PATH}"
        ),
    )

    dq = BashOperator(
        task_id="dq",
        bash_command=(
            f"{COMMON_PREFIX} && "
            f"python src/etl_steps.py dq --config {CONFIG_PATH}"
        ),
    )

    extract >> transform >> load >> dq
