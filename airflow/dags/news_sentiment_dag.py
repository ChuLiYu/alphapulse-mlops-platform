from airflow.decorators import dag, task
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
import pandas as pd

from alphapulse_utils.news_fetcher import fetch_unprocessed_news
from alphapulse_utils.sentiment_analyzer import SentimentAnalyzer
from alphapulse_utils.news_exporters import save_sentiment_scores

@dag(
    dag_id='news_sentiment_pipeline',
    schedule_interval='*/30 * * * *', # Every 30 minutes
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,
    tags=['alphapulse', 'sentiment', 'ml'],
    default_args={
        'owner': 'airflow',
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    }
)
def news_sentiment():

    @task(task_id='load_unprocessed_news')
    def load_news():
        df = fetch_unprocessed_news()
        for col in df.select_dtypes(include=['datetime', 'datetimetz']).columns:
            df[col] = df[col].astype(str)
        return df.to_dict(orient='records')

    @task(task_id='analyze_news_sentiment')
    def analyze_sentiment(data):
        df = pd.DataFrame(data)
        analyzer = SentimentAnalyzer()
        result_df = analyzer.analyze_dataframe(df)
        for col in result_df.select_dtypes(include=['datetime', 'datetimetz']).columns:
            result_df[col] = result_df[col].astype(str)
        return result_df.to_dict(orient='records')

    @task(task_id='save_sentiment_scores')
    def save_scores(data):
        df = pd.DataFrame(data)
        if 'analyzed_at' in df.columns:
            df['analyzed_at'] = pd.to_datetime(df['analyzed_at'])
        save_sentiment_scores(df)

    # flow
    news_data = load_news()
    scored_data = analyze_sentiment(news_data)
    save_scores(scored_data)

dag = news_sentiment()
