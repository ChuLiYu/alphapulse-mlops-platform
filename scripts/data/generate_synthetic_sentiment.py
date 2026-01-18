import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random


def generate_hourly_synthetic_data():
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse"
    )
    engine = create_engine(db_url)

    print("🧹 Cleaning old synthetic data...")
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM news_sentiment WHERE source LIKE 'Synthetic%';"))
        conn.commit()

    print("📥 Loading hourly price timestamps...")
    with engine.connect() as conn:
        # We only need the dates/times, not the prices
        time_df = pd.read_sql("SELECT date FROM btc_price_data ORDER BY date", conn)

    if time_df.empty:
        print("❌ No price data found. Cannot align synthetic sentiment.")
        return

    print(f"✅ Found {len(time_df)} hours to process.")

    sources = ["Synthetic_Twitter", "Synthetic_Reddit", "Synthetic_News"]
    topics = ["Regulation", "Technology", "Adoption", "Macro", "Security", "General"]

    synthetic_records = []

    print("🏗️ Generating hourly synthetic sentiment (Random distribution)...")

    # Probability of having a news item in any given hour (e.g., 0.125 means ~1 item every 8 hours)
    prob_per_hour = 0.125

    for _, row in time_df.iterrows():
        if random.random() > prob_per_hour:
            continue

        date = row["date"]
        source = random.choice(sources)
        topic = random.choice(topics)

        # COMPLETELY RANDOM Sentiment (30% Pos, 30% Neg, 40% Neu)
        rand_val = random.random()
        if rand_val < 0.3:
            sentiment = "positive"
            score = random.uniform(0.1, 0.8)
        elif rand_val < 0.6:
            sentiment = "negative"
            score = random.uniform(-0.8, -0.1)
        else:
            sentiment = "neutral"
            score = random.uniform(-0.1, 0.1)

        synthetic_records.append(
            {
                "symbol": "BTC",
                "title": f"[SYNTHETIC_{topic}] Hourly market update",
                "content": f"Automated hourly benchmark data. Topic: {topic}.",
                "url": f"http://synthetic.alphapulse.com/{source.lower()}/{date.strftime('%Y%m%d%H')}",
                "source": source,
                "sentiment_score": score,
                "sentiment_label": sentiment,
                "sentiment_confidence": random.uniform(0.7, 0.95),
                "published_at": date,
                "analyzed_at": datetime.now(),
            }
        )

    print(f"✅ Generated {len(synthetic_records)} hourly records.")

    # Bulk insert in chunks
    df_synthetic = pd.DataFrame(synthetic_records)

    print(f"💾 Inserting into news_sentiment...")
    with engine.connect() as conn:
        df_synthetic.to_sql("temp_synthetic", engine, if_exists="replace", index=False)

        upsert_query = text("""
            INSERT INTO news_sentiment (symbol, title, content, url, source, sentiment_score, sentiment_label, sentiment_confidence, published_at, analyzed_at)
            SELECT symbol, title, content, url, source, sentiment_score, sentiment_label, sentiment_confidence, published_at, analyzed_at
            FROM temp_synthetic
            ON CONFLICT (url) DO NOTHING;
        """)

        conn.execute(upsert_query)
        conn.execute(text("DROP TABLE temp_synthetic;"))
        conn.commit()

    print(f"🚀 Successfully integrated hourly average synthetic data!")


if __name__ == "__main__":
    generate_hourly_synthetic_data()
