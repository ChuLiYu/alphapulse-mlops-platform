from airflow.decorators import dag, task
from datetime import datetime, timedelta
import requests
import os
import json

@dag(
    dag_id='model_training_pipeline',
    schedule_interval='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    is_paused_upon_creation=False,
    tags=['alphapulse', 'ml', 'training'],
    default_args={
        'owner': 'airflow',
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    }
)
def training_pipeline():

    @task(task_id='trigger_training_job')
    def trigger_training(**context):
        # Get mode from dag_run.conf or default to ultra_fast
        dag_run = context.get('dag_run')
        mode = "ultra_fast"
        if dag_run and dag_run.conf and 'mode' in dag_run.conf:
            mode = dag_run.conf['mode']
            
        # Require trainer URL to be set explicitly
        trainer_url = os.getenv("TRAINER_API_URL")
        if not trainer_url:
            raise ValueError("TRAINER_API_URL environment variable is required but not set")
        endpoint = f"{trainer_url}/train"
        
        payload = {
            "mode": mode,
            "experiment_name": f"airflow_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        print(f"Triggering training at {endpoint} with payload {payload}")
        
        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            print(f"Training triggered successfully: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error triggering training: {e}")
            raise

    trigger_training()

training_dag = training_pipeline()
