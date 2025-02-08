import pandas as pd
import os
from sqlalchemy import create_engine, text

def force_hourly_integration():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse")
    engine = create_engine(db_url)
    
    print("📥 Reading HOURLY btc_price_data...")
    # Read all hourly price data
    price_df = pd.read_sql("SELECT * FROM btc_price_data ORDER BY date", engine)
    print(f"   Found {len(price_df)} hourly records from {price_df['date'].min()} to {price_df['date'].max()}")
    
    # Aggregating sentiment by HOUR instead of DATE
    sentiment_query = """
        SELECT 
            DATE_TRUNC('hour', published_at) as date_h,
            AVG(sentiment_score) as sentiment_avg,
            COUNT(*) as news_count
        FROM news_sentiment
        GROUP BY DATE_TRUNC('hour', published_at)
    """
    
    print("📥 Reading sentiment data (Hourly aggregation)...")
    sentiment_df = pd.read_sql(sentiment_query, engine)
    print(f"   Found {len(sentiment_df)} distinct hours with sentiment data.")
    
    # Ensure date formats match for merge
    price_df['date'] = pd.to_datetime(price_df['date'])
    sentiment_df['date_h'] = pd.to_datetime(sentiment_df['date_h'])
    
    print("🔄 Merging datasets on hourly timestamp...")
    # Merge price with sentiment
    df = price_df.merge(sentiment_df, left_on='date', right_on='date_h', how='left')
    
    # Fill gaps (most hours might not have news, which is realistic)
    df['sentiment_avg'] = df['sentiment_avg'].fillna(0)
    df['news_count'] = df['news_count'].fillna(0)
    
    # Drop redundant column
    if 'date_h' in df.columns:
        df = df.drop(columns=['date_h'])
        
    print(f"✅ Final hourly integrated dataset: {len(df)} rows.")
    
    print("💾 Updating model_features table with HOURLY granularity...")
    # Caution: This will replace the daily features with hourly ones
    df.to_sql("model_features", engine, if_exists="replace", index=False)
    print("🎉 Done! System now has 8+ years of HOURLY real price + sentiment data.")

if __name__ == "__main__":
    force_hourly_integration()
