import pandas as pd
from operators.postgres_operator import PostgresUtils
from sqlalchemy import text

def create_news_tables_if_not_exist():
    engine = PostgresUtils.get_sqlalchemy_engine()
    
    queries = [
        """
        CREATE TABLE IF NOT EXISTS market_news (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            summary TEXT,
            published_at TIMESTAMP,
            source TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_market_news_source ON market_news(source);",
        "CREATE INDEX IF NOT EXISTS idx_market_news_published_at ON market_news(published_at DESC);",
        """
        CREATE TABLE IF NOT EXISTS sentiment_scores (
            id SERIAL PRIMARY KEY,
            article_id INTEGER NOT NULL REFERENCES market_news(id),
            sentiment_score FLOAT NOT NULL,
            confidence FLOAT NOT NULL,
            label TEXT NOT NULL,
            analyzed_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(article_id)
        );
        """
    ]
    
    with engine.begin() as conn:
        for q in queries:
            conn.execute(text(q))

def export_news_to_postgres(df: pd.DataFrame):
    if df.empty:
        return
        
    create_news_tables_if_not_exist()
    
    engine = PostgresUtils.get_sqlalchemy_engine()
    
    # Using raw SQL for ON CONFLICT DO NOTHING
    # Assuming df has 'title', 'url', ...
    with engine.begin() as conn:
        for _, row in df.iterrows():
            stmt = text("""
                INSERT INTO market_news (title, url, summary, published_at, source)
                VALUES (:title, :url, :summary, :published_at, :source)
                ON CONFLICT (url) DO NOTHING
            """)
            conn.execute(stmt, {
                "title": row["title"],
                "url": row["url"],
                "summary": row["summary"],
                "published_at": row["published_at"],
                "source": row["source"]
            })

def save_sentiment_scores(df: pd.DataFrame):
    if df.empty:
        return

    create_news_tables_if_not_exist()
    
    engine = PostgresUtils.get_sqlalchemy_engine()
    
    with engine.begin() as conn:
        for _, row in df.iterrows():
            stmt = text("""
                INSERT INTO sentiment_scores 
                (article_id, sentiment_score, confidence, label, analyzed_at)
                VALUES (:article_id, :sentiment_score, :confidence, :label, :analyzed_at)
                ON CONFLICT (article_id) DO NOTHING
            """)
            conn.execute(stmt, {
                "article_id": row["article_id"],
                "sentiment_score": row["sentiment_score"],
                "confidence": row["confidence"],
                "label": row["label"],
                "analyzed_at": row["analyzed_at"]
            })
