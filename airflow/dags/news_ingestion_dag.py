from airflow.decorators import dag, task
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
import pandas as pd

from alphapulse_utils.news_fetcher import fetch_rss_feeds
from alphapulse_utils.news_exporters import export_news_to_postgres

@dag(
    dag_id='news_ingestion_pipeline',
    schedule_interval='*/30 * * * *', # Every 30 minutes
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,
    tags=['alphapulse', 'news'],
    default_args={
        'owner': 'airflow',
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
    }
)
def news_ingestion():

    @task(task_id='load_rss_feeds')
    def load_feeds():
        df = fetch_rss_feeds()
        # Convert datetime objects to strings for XCom serialization
        for col in df.select_dtypes(include=['datetime', 'datetimetz']).columns:
            df[col] = df[col].astype(str)
        return df.to_dict(orient='records')

    @task(task_id='export_to_postgres')
    def save_news(data):
        df = pd.DataFrame(data)
        if 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at'])
        export_news_to_postgres(df)

    # flow
    news_data = load_feeds()
    save_news(news_data)

dag = news_ingestion()
