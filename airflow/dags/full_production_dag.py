from airflow.decorators import dag, task
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
import requests
import os


@dag(
    dag_id="full_production_pipeline",
    schedule_interval="0 */4 * * *",  # Every 4 hours
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,
    tags=["alphapulse", "production", "e2e"],
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=10),
    },
)
def full_production_pipeline():

    @task(task_id="collect_price_data")
    def trigger_price_ingestion():
        from alphapulse_utils.btc_fetcher import load_btc_data
        from alphapulse_utils.indicators import calculate_indicators
        from alphapulse_utils.db_exporters import export_indicators_to_postgres

        print("Fetching latest BTC prices...")
        raw_data = load_btc_data()
        indicators = calculate_indicators(raw_data)
        export_indicators_to_postgres(indicators)
        return True

    @task(task_id="collect_news_data")
    def trigger_news_ingestion():
        from alphapulse_utils.news_fetcher import fetch_rss_feeds
        from alphapulse_utils.news_exporters import export_news_to_postgres

        print("Fetching latest market news...")
        news_df = fetch_rss_feeds()
        export_news_to_postgres(news_df)
        return True

    @task(task_id="integrate_features")
    def trigger_integration(price_ok, news_ok):
        from alphapulse_utils.feature_integrator import integrate_sentiment_features

        print("Integrating features...")
        integrate_sentiment_features()
        return True

    @task(task_id="train_and_deploy")
    def trigger_training(feat_ok):
        trainer_url = os.getenv("TRAINER_API_URL", "http://trainer:8080")
        endpoint = f"{trainer_url}/train"

        payload = {
            "mode": "quick_production",
            "experiment_name": f"auto_prod_{datetime.now().strftime('%Y%m%d_%H%M')}",
        }

        response = requests.post(endpoint, json=payload, timeout=60)
        response.raise_for_status()
        print(f"Training/Deployment triggered: {response.json()}")
        return response.json()

    @task(task_id="monitor_drift")
    def run_monitoring(train_res):
        from src.alphapulse.monitoring.drift_detector import DriftDetector

        print("Running data drift analysis...")
        detector = DriftDetector()
        report = detector.run_drift_analysis()
        return report

    @task(task_id="generate_live_signal")
    def run_inference(mon_res):
        from src.alphapulse.ml.inference.engine import InferenceEngine

        print("Generating live trading signals...")
        engine = InferenceEngine()
        signal = engine.generate_signals()
        print(f"Latest Signal: {signal}")
        return signal

    # Flow
    p_ok = trigger_price_ingestion()
    n_ok = trigger_news_ingestion()
    f_ok = trigger_integration(p_ok, n_ok)
    train_res = trigger_training(f_ok)
    mon_res = run_monitoring(train_res)
    run_inference(mon_res)


dag = full_production_pipeline()
