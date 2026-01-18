import os
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text


def get_database_url():
    """Get database URL based on environment."""
    return os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse"
    )


def load_data():
    """Load data from database."""
    print("Loading data from database...")

    # Create engine directly
    engine = create_engine(get_database_url())
    db = engine.connect()

    try:
        # Load Prices
        query_prices = text("SELECT * FROM prices ORDER BY timestamp")
        df_prices = pd.read_sql(query_prices, db)

        # Load Indicators
        query_indicators = text("SELECT * FROM technical_indicators ORDER BY timestamp")
        df_indicators = pd.read_sql(query_indicators, db)

        # Load Sentiment
        # Join sentiment_scores with market_news to get published_at if needed,
        # but analyzed_at is usually good enough for feature engineered time.
        # We use analyzed_at because that's when the info becomes available to the system.
        query_sentiment = text("""
            SELECT ss.sentiment_score, ss.confidence, ss.label, ss.analyzed_at
            FROM sentiment_scores ss
            ORDER BY ss.analyzed_at
        """)
        df_sentiment = pd.read_sql(query_sentiment, db)
        df_sentiment["analyzed_at"] = pd.to_datetime(df_sentiment["analyzed_at"])

        print(
            f"Loaded {len(df_prices)} prices, {len(df_indicators)} indicators, and {len(df_sentiment)} sentiment records."
        )
        return df_prices, df_indicators, df_sentiment
    finally:
        db.close()


def calculate_sentiment_features(price_df, sentiment_df):
    """
    Calculate window-based sentiment features for each price row.
    This is a simplified version of the logic in feature_integration_pipeline.
    """
    if sentiment_df.empty:
        print("Warning: No sentiment data available. Filling with neutrals.")
        df = price_df.copy()
        df["sentiment_avg_24h"] = 0
        df["sentiment_volatility_24h"] = 0
        df["sentiment_momentum_24h"] = 0
        return df

    print("Calculating sentiment features (this may take a moment)...")
    result_df = price_df.copy()

    # Sort for efficient search
    sentiment_df = sentiment_df.sort_values("analyzed_at")

    # Pre-calculate rolling features could be faster, but let's stick to the window iteration
    # for correctness with irregular timestamps, similar to the pipeline logic.
    # To speed it up, we can use asof merge or resample if data is dense,
    # but for now let's use a simple iterative approach or apply.

    # Optimization: Resample sentiment to hourly first to speed up lookup
    sent_hourly = (
        sentiment_df.set_index("analyzed_at")
        .resample("1h")
        .agg({"sentiment_score": ["mean", "std", "count"]})
    )
    sent_hourly.columns = ["hourly_mean", "hourly_std", "hourly_count"]
    sent_hourly = sent_hourly.fillna(0)

    # Now valid timestamps in price_df using asof merge from re-indexed sentiment
    # But wait, we need rolling windows (24h).
    # Let's compute rolling 24h on the hourly resampled data first.

    sent_hourly["rolling_mean_24h"] = (
        sent_hourly["hourly_mean"].rolling(window=24, min_periods=1).mean()
    )
    sent_hourly["rolling_std_24h"] = (
        sent_hourly["hourly_mean"].rolling(window=24, min_periods=1).std()
    )

    # Momentum: (Current 24h mean) - (Previous 24h mean shifted by 24h)
    sent_hourly["momentum_24h"] = sent_hourly["rolling_mean_24h"] - sent_hourly[
        "rolling_mean_24h"
    ].shift(24)

    sent_hourly = sent_hourly.fillna(0).reset_index()

    # Merge price_df with the closest previous hourly sentiment
    result_df = pd.merge_asof(
        result_df.sort_values("timestamp"),
        sent_hourly,
        left_on="timestamp",
        right_on="analyzed_at",
        direction="backward",
    )

    # Rename columns to match expected feature names
    result_df.rename(
        columns={
            "rolling_mean_24h": "sentiment_avg_24h",
            "rolling_std_24h": "sentiment_volatility_24h",
            "momentum_24h": "sentiment_momentum_24h",
        },
        inplace=True,
    )

    # Cleanup
    drop_cols = ["analyzed_at", "hourly_mean", "hourly_std", "hourly_count"]
    result_df.drop(
        columns=[c for c in drop_cols if c in result_df.columns], inplace=True
    )

    return result_df


def add_news_frequency_features(price_df):
    """
    Add news frequency features by querying market_news table.

    Args:
        price_df: DataFrame with price and timestamp data

    Returns:
        DataFrame with added news frequency features
    """
    try:
        engine = create_engine(get_database_url())

        # Get date range
        min_date = price_df["timestamp"].min()
        max_date = price_df["timestamp"].max()

        # Load news data
        query = text("""
            SELECT published_at, source
            FROM market_news
            WHERE published_at >= :min_date
                AND published_at <= :max_date
            ORDER BY published_at
        """)

        news_df = pd.read_sql(
            query, engine, params={"min_date": min_date, "max_date": max_date}
        )

        if news_df.empty:
            print("No news data available. Adding zero-filled news features.")
            price_df["news_count_1h"] = 0
            price_df["news_count_24h"] = 0
            price_df["news_count_7d"] = 0
            price_df["news_velocity_24h"] = 0
            return price_df

        news_df["published_at"] = pd.to_datetime(news_df["published_at"])
        print(f"Loaded {len(news_df)} news articles for feature engineering")

        # Sort both dataframes
        price_df = price_df.sort_values("timestamp")
        news_df = news_df.sort_values("published_at")

        # Calculate news counts for each price timestamp
        news_counts_1h = []
        news_counts_24h = []
        news_counts_7d = []
        news_velocity_24h = []

        for ts in price_df["timestamp"]:
            # 1 hour window
            count_1h = len(
                news_df[news_df["published_at"].between(ts - timedelta(hours=1), ts)]
            )

            # 24 hour window
            news_24h = news_df[
                news_df["published_at"].between(ts - timedelta(days=1), ts)
            ]
            count_24h = len(news_24h)

            # 7 day window
            count_7d = len(
                news_df[news_df["published_at"].between(ts - timedelta(days=7), ts)]
            )

            # News velocity (articles per hour in last 24h)
            velocity_24h = count_24h / 24.0 if count_24h > 0 else 0.0

            news_counts_1h.append(count_1h)
            news_counts_24h.append(count_24h)
            news_counts_7d.append(count_7d)
            news_velocity_24h.append(velocity_24h)

        price_df["news_count_1h"] = news_counts_1h
        price_df["news_count_24h"] = news_counts_24h
        price_df["news_count_7d"] = news_counts_7d
        price_df["news_velocity_24h"] = news_velocity_24h

        # News-Price Interaction Features
        if "atr_14" in price_df.columns:
            price_df["news_volatility_interaction"] = (
                price_df["news_count_24h"] * price_df["atr_14"]
            )

        print(f"Added news frequency features")
        engine.dispose()

    except Exception as e:
        print(f"Warning: Could not add news features: {e}")
        price_df["news_count_1h"] = 0
        price_df["news_count_24h"] = 0
        price_df["news_count_7d"] = 0
        price_df["news_velocity_24h"] = 0

    return price_df


def prepare_features(df_prices, df_indicators, df_sentiment=None):
    """Merge and prepare features."""
    print("Preparing features...")

    # Ensure timestamps are datetime
    df_prices["timestamp"] = pd.to_datetime(df_prices["timestamp"])
    df_indicators["timestamp"] = pd.to_datetime(df_indicators["timestamp"])

    print(
        f"Prices range: {df_prices['timestamp'].min()} to {df_prices['timestamp'].max()}"
    )
    print(
        f"Indicators range: {df_indicators['timestamp'].min()} to {df_indicators['timestamp'].max()}"
    )

    # Merge on symbol and timestamp
    df = pd.merge(
        df_prices, df_indicators, on=["symbol", "timestamp"], suffixes=("", "_dup")
    )

    # Drop duplicate columns
    df = df.loc[:, ~df.columns.str.endswith("_dup")]

    print(f"Merged price/indicators shape: {df.shape}")

    # Integrate Sentiment Features
    if df_sentiment is not None and not df_sentiment.empty:
        df = calculate_sentiment_features(df, df_sentiment)
        print(f"Shape after sentiment merge: {df.shape}")
    else:
        # Add placeholders if no sentiment
        print("Adding placeholder sentiment features")
        df["sentiment_avg_24h"] = 0.0
        df["sentiment_volatility_24h"] = 0.0
        df["sentiment_momentum_24h"] = 0.0

    # Convert Decimal to float for ML
    numeric_cols = df.select_dtypes(include=["object"]).columns
    for col in numeric_cols:
        try:
            df[col] = df[col].astype(float)
        except (ValueError, TypeError):
            pass  # Keep as is (e.g. symbol)

    # Sort
    df.sort_values("timestamp", inplace=True)

    # === ENHANCED FEATURE ENGINEERING ===

    # 1. Add Cross Features (Interaction Terms)
    print("Adding interaction features...")

    # Price-Volatility Interaction
    if "atr_14" in df.columns:
        df["price_volatility_ratio"] = df["price"] / (df["atr_14"] + 1e-8)

    # Sentiment-Volatility Interaction
    if "sentiment_avg_24h" in df.columns and "atr_14" in df.columns:
        df["sentiment_volatility_interaction"] = df["sentiment_avg_24h"] * df["atr_14"]
        df["sentiment_volatility_ratio"] = df["sentiment_avg_24h"] / (
            df["atr_14"] + 1e-8
        )

    # RSI-Sentiment Alignment
    if "rsi_14" in df.columns and "sentiment_avg_24h" in df.columns:
        # Normalize RSI to [-1, 1] range: (RSI - 50) / 50
        df["rsi_normalized"] = (df["rsi_14"] - 50) / 50
        df["sentiment_rsi_alignment"] = df["sentiment_avg_24h"] * df["rsi_normalized"]
        df["sentiment_rsi_divergence"] = abs(
            df["sentiment_avg_24h"] - df["rsi_normalized"]
        )

    # MACD-Sentiment Interaction
    if "macd_histogram" in df.columns and "sentiment_avg_24h" in df.columns:
        df["macd_sentiment_interaction"] = (
            df["macd_histogram"] * df["sentiment_avg_24h"]
        )

    # Volume-Sentiment Interaction
    if "volume" in df.columns and "sentiment_avg_24h" in df.columns:
        df["volume_sentiment_interaction"] = df["volume"] * df["sentiment_avg_24h"]

    # Momentum Features
    if "sma_7" in df.columns and "sma_25" in df.columns:
        df["sma_7_25_ratio"] = df["sma_7"] / (df["sma_25"] + 1e-8)
        df["price_sma7_distance"] = (df["price"] - df["sma_7"]) / (df["sma_7"] + 1e-8)
        df["price_sma25_distance"] = (df["price"] - df["sma_25"]) / (
            df["sma_25"] + 1e-8
        )

    # Sentiment Momentum Squared (amplify strong sentiment changes)
    if "sentiment_momentum_24h" in df.columns:
        df["sentiment_momentum_squared"] = df["sentiment_momentum_24h"] ** 2
        df["sentiment_momentum_sign"] = np.sign(df["sentiment_momentum_24h"])

    # Price Momentum
    df["price_momentum_1d"] = df.groupby("symbol")["price"].pct_change(1)
    df["price_momentum_7d"] = df.groupby("symbol")["price"].pct_change(7)

    # Volatility of Returns (rolling std)
    df["return_volatility_7d"] = (
        df.groupby("symbol")["price"]
        .pct_change()
        .rolling(7)
        .std()
        .reset_index(0, drop=True)
    )

    # 2. Add News Frequency Features (if market_news data exists)
    print("Attempting to add news frequency features...")
    df = add_news_frequency_features(df)

    print(f"Features after enhancement: {df.shape[1]} columns")

    # Feature Engineering
    # Target: Next Day Return (Percent Change)
    # We want to predict tomorrow's return based on today's data
    df["target"] = df.groupby("symbol")["price"].transform(
        lambda x: x.pct_change().shift(-1)
    )

    # Target: Next Day Return (Percent Change)
    # We want to predict tomorrow's return based on today's data
    df["target"] = df.groupby("symbol")["price"].transform(
        lambda x: x.pct_change().shift(-1)
    )

    print("DEBUG: NaN counts before drop:")
    print(df.isnull().sum())

    # Drop rows with NaN target only initially, to see if other cols are issues
    df.dropna(subset=["target"], inplace=True)

    # Fill other NaNs with 0 if any (indicators shouldn't have them)
    df.fillna(0, inplace=True)

    print(f"Feature set shape after cleanup: {df.shape}")
    return df


def save_splits(df, output_dir="/app/src/data/processed"):
    """Split data and save to Parquet."""
    print(f"Splitting and saving to {output_dir}...")

    # Support both container and host paths
    if not os.path.exists(output_dir):
        output_dir = "/home/src/data/processed"  # Container path

    os.makedirs(output_dir, exist_ok=True)

    # Time-series split (no shuffle)
    # Train: 70%, Val: 15%, Test: 15%
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]

    print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

    train.to_parquet(f"{output_dir}/train.parquet", index=False)
    val.to_parquet(f"{output_dir}/val.parquet", index=False)
    test.to_parquet(f"{output_dir}/test.parquet", index=False)
    print("Data saved successfully.")


def main():
    df_prices, df_indicators, df_sentiment = load_data()
    if df_prices.empty or df_indicators.empty:
        print("Error: No data found in database.")
        return

    df_full = prepare_features(df_prices, df_indicators, df_sentiment)
    save_splits(df_full)


if __name__ == "__main__":
    main()
