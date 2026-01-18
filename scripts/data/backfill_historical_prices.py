import yfinance as yf
import pandas as pd
import os
from sqlalchemy import create_engine, text
from datetime import datetime


def backfill_btc_prices():
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse"
    )
    engine = create_engine(db_url)

    print("🚀 Fetching real historical BTC-USD data from Yahoo Finance...")
    # Get 10 years of data
    btc = yf.download(
        "BTC-USD", start="2016-01-01", end=datetime.now().strftime("%Y-%m-%d")
    )

    if btc.empty:
        print("❌ Failed to fetch data from Yahoo Finance.")
        return

    # Process multi-index columns if they exist (yfinance quirk)
    if isinstance(btc.columns, pd.MultiIndex):
        btc.columns = btc.columns.get_level_values(0)

    # Flatten and clean
    btc = btc.reset_index()
    btc.columns = [c.lower() for c in btc.columns]

    # Map columns to schema
    # Expected columns: date, ticker, open, high, low, close, volume, daily_return, data_source
    df = pd.DataFrame()
    df["date"] = btc["date"]
    df["ticker"] = "BTC"
    df["open"] = btc["open"]
    df["high"] = btc["high"]
    df["low"] = btc["low"]
    df["close"] = btc["close"]
    df["volume"] = btc["volume"]
    df["data_source"] = "YahooFinance"

    # Calculate returns
    df["daily_return"] = df["close"].pct_change()
    df["log_return"] = df["daily_return"].apply(
        lambda x: (
            0
            if x <= -1
            else (
                0
                if pd.isna(x)
                else (float(x) if x == 0 else (pd.NA if x < -1 else (pd.NA)))
            )
        )
    )  # Dummy for now
    # Re-calculate clean log returns
    import numpy as np

    df["log_return"] = np.log(df["close"] / df["close"].shift(1))

    df = df.fillna(0)

    print(f"✅ Processed {len(df)} days of real price data.")

    # Insert using Upsert logic
    with engine.connect() as conn:
        df.to_sql("temp_prices", engine, if_exists="replace", index=False)

        upsert_query = text("""
            INSERT INTO btc_price_data (date, ticker, open, high, low, close, volume, daily_return, log_return, data_source)
            SELECT date, ticker, open, high, low, close, volume, daily_return, log_return, data_source
            FROM temp_prices
            ON CONFLICT (date, ticker) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                daily_return = EXCLUDED.daily_return,
                log_return = EXCLUDED.log_return,
                data_source = EXCLUDED.data_source;
        """)

        conn.execute(upsert_query)
        conn.execute(text("DROP TABLE temp_prices;"))
        conn.commit()

    print(
        f"🎉 Successfully backfilled {len(df)} days of real BTC price data into the system!"
    )


if __name__ == "__main__":
    backfill_btc_prices()
