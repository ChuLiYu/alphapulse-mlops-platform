import pandas as pd
import logging
import numpy as np
from sqlalchemy import text
from operators.postgres_operator import PostgresUtils

from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)

def integrate_sentiment_features():
    """
    Acts as the 'Feature Producer' for the Feature Store.
    Calculates standardized features and persists them.
    """
    try:
        from alphapulse.ml.features.feature_producer import FeatureProducer
        hook = PostgresHook(postgres_conn_id='postgres_default')
        engine = hook.get_sqlalchemy_engine()
        
        # Load raw data
        price_df = hook.get_pandas_df("SELECT * FROM btc_price_data ORDER BY date")
        sentiment_query = "SELECT DATE_TRUNC('hour', published_at) as date_h, AVG(sentiment_score) as sentiment_avg, COUNT(*) as news_count FROM news_sentiment GROUP BY 1"
        sentiment_df = hook.get_pandas_df(sentiment_query)
        
        if price_df.empty:
            logger.warning("No price data found.")
            return False

        # Produce standardized features
        producer = FeatureProducer()
        feature_df = producer.produce_stationary_features(price_df, sentiment_df)
        
        # Persist to 'feature_store' table (Single Source of Truth)
        feature_df.to_sql("feature_store", engine, if_exists="replace", index=False)
        
        # Also update 'model_features' for backward compatibility
        feature_df.to_sql("model_features", engine, if_exists="replace", index=False)
        
        logger.info(f"✅ Feature Store updated. Total materialized rows: {len(feature_df)}")
        return True
    except Exception as e:
        logger.error(f"Error in feature store materialization: {e}")
        raise

    except Exception as e:
        logger.error(f"Error integrating sentiment features: {e}")
        raise
