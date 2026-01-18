from airflow.decorators import dag, task
from datetime import datetime, timedelta
import pandas as pd
from airflow.utils.dates import days_ago
import sys
import os

# Add airflow/utils to sys path if needed, or rely on installation
# Assuming airflow/utils is in pythonpath or we import relatively
from alphapulse_utils.btc_fetcher import load_btc_data
from alphapulse_utils.indicators import calculate_indicators
from alphapulse_utils.db_exporters import export_indicators_to_postgres
from operators.minio_operator import MinIOUtils


@dag(
    dag_id="btc_price_pipeline",
    schedule_interval="@hourly",
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,
    tags=["alphapulse", "btc", "financial"],
    default_args={
        "owner": "airflow",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
)
def btc_price_pipeline():

    @task(task_id="load_btc_data")
    def load_data_task():
        df = load_btc_data()
        # Serialize to dict for XCom
        for col in df.select_dtypes(include=["datetime", "datetimetz"]).columns:
            df[col] = df[col].astype(str)
        return df.to_dict(orient="records")

    @task(task_id="calculate_technical_indicators")
    def calculate_indicators_task(data):
        df = pd.DataFrame(data)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        df_indicators = calculate_indicators(df)
        for col in df_indicators.select_dtypes(
            include=["datetime", "datetimetz"]
        ).columns:
            df_indicators[col] = df_indicators[col].astype(str)
        return df_indicators.to_dict(orient="records")

    @task(task_id="save_to_postgres")
    def save_to_postgres_task(data):
        df = pd.DataFrame(data)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        export_indicators_to_postgres(df)

    @task(task_id="save_to_minio")
    def save_to_minio_task(data):
        df = pd.DataFrame(data)
        object_name = (
            f'btc_price_indicators_{pd.Timestamp.now().strftime("%Y%m%d%H%M%S")}.csv'
        )
        MinIOUtils.save_df_to_minio(df, "raw-data", object_name)

    # DAG Flow
    raw_data = load_data_task()
    indicators = calculate_indicators_task(raw_data)

    save_to_postgres_task(indicators)
    save_to_minio_task(indicators)


dag = btc_price_pipeline()
