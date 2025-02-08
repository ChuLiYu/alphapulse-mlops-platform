from airflow.decorators import dag, task
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
import pandas as pd

from alphapulse_utils.feature_integrator import integrate_sentiment_features

@dag(
    dag_id='feature_integration_pipeline',
    schedule_interval='0 4 * * *', # Daily at 4 AM (after price and news are likely collected)
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,
    tags=['alphapulse', 'data', 'features'],
    default_args={
        'owner': 'airflow',
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    }
)
def feature_integration():

    @task(task_id='integrate_features')
    def integrate_task():
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Starting feature integration process")
            success = integrate_sentiment_features()
            
            if not success:
                error_msg = "Feature integration failed - possibly no data available or integration error"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info("Feature integration completed successfully")
            return success
            
        except Exception as e:
            logger.error(f"Feature integration failed with exception: {str(e)}")
            raise

    integrate_task()

dag = feature_integration()
