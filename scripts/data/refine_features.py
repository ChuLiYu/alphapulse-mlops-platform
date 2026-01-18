import pandas as pd
import numpy as np
import os
import sys
from sqlalchemy import create_engine

# Add src to path to load the producer
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)
from alphapulse.ml.features.feature_producer import FeatureProducer


def materialize_feature_store():
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse"
    )
    engine = create_engine(db_url)

    print("🚀 Feature Store Materialization Started...")

    # Load raw data
    print("   📥 Fetching raw data from DB...")
    price_df = pd.read_sql("SELECT * FROM btc_price_data ORDER BY date", engine)

    sentiment_query = """
        SELECT 
            DATE_TRUNC('hour', published_at) as date_h,
            AVG(sentiment_score) as sentiment_avg,
            COUNT(*) as news_count
        FROM news_sentiment
        GROUP BY 1
    """
    sentiment_df = pd.read_sql(sentiment_query, engine)

    # Process
    print("   🧪 Generating 50+ standardized features...")
    producer = FeatureProducer()
    feat_df = producer.produce_stationary_features(price_df, sentiment_df)

    # Safety: Drop rows with NaNs from calculations
    feat_df = feat_df.dropna().reset_index(drop=True)

    # Save
    print(
        f"   💾 Materializing {len(feat_df)} rows with {len(feat_df.columns)-4} features..."
    )
    feat_df.to_sql("feature_store", engine, if_exists="replace", index=False)
    feat_df.to_sql("model_features", engine, if_exists="replace", index=False)

    print("✅ Feature Store is now fully aligned and populated!")


if __name__ == "__main__":
    materialize_feature_store()
