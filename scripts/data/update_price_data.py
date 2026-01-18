#!/usr/bin/env python3
"""
Automated price data collection from Yahoo Finance.
Updates the prices table with latest BTC-USD data.
"""

import sys

sys.path.insert(0, "/home/src/src")

import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_latest_prices(days_back: int = 7):
    """
    Collect latest BTC price data.

    Args:
        days_back: Number of days to look back
    """
    logger.info(f"📈 Collecting BTC price data (last {days_back} days)...")

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Fetch data from Yahoo Finance
        logger.info(f"  Fetching from {start_date.date()} to {end_date.date()}")
        ticker = yf.Ticker("BTC-USD")
        df = ticker.history(start=start_date, end=end_date, interval="1d")

        if df.empty:
            logger.warning("  No data returned from Yahoo Finance")
            return False

        logger.info(f"  ✅ Fetched {len(df)} records")

        # Prepare data for database
        df = df.reset_index()
        df = df.rename(
            columns={
                "Date": "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "price",
                "Volume": "volume",
            }
        )

        # Add symbol
        df["symbol"] = "BTC-USD"
        df["created_at"] = datetime.now()

        # Select required columns
        df = df[
            [
                "timestamp",
                "symbol",
                "open",
                "high",
                "low",
                "price",
                "volume",
                "created_at",
            ]
        ]

        # Connect to database
        import os

        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse"
        )
        engine = create_engine(db_url)

        # Insert data (avoiding duplicates)
        logger.info("  💾 Saving to database...")

        with engine.connect() as conn:
            # Create temp table
            df.to_sql("temp_prices", conn, if_exists="replace", index=False)

            # Insert only new records
            result = conn.execute(text("""
                INSERT INTO prices (timestamp, symbol, open, high, low, price, volume, created_at)
                SELECT timestamp, symbol, open, high, low, price, volume, created_at
                FROM temp_prices
                WHERE NOT EXISTS (
                    SELECT 1 FROM prices p 
                    WHERE p.timestamp = temp_prices.timestamp 
                    AND p.symbol = temp_prices.symbol
                )
                ON CONFLICT (timestamp, symbol) DO UPDATE
                SET price = EXCLUDED.price,
                    volume = EXCLUDED.volume,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    open = EXCLUDED.open
            """))
            conn.commit()

            new_count = result.rowcount
            logger.info(f"  ✅ Inserted/Updated {new_count} records")

            # Clean up temp table
            conn.execute(text("DROP TABLE IF EXISTS temp_prices"))
            conn.commit()

        # Show latest price
        with engine.connect() as conn:
            latest = conn.execute(text("""
                SELECT timestamp, price, volume 
                FROM prices 
                WHERE symbol = 'BTC-USD' 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)).fetchone()

            if latest:
                logger.info(f"\n  📊 Latest Price:")
                logger.info(f"    Date: {latest[0]}")
                logger.info(f"    Price: ${latest[1]:,.2f}")
                logger.info(f"    Volume: {latest[2]:,.0f}")

        return True

    except Exception as e:
        logger.error(f"❌ Error collecting prices: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main execution."""
    print("=" * 60)
    print("📈 BTC Price Data Collection")
    print("=" * 60)
    print()

    success = collect_latest_prices(days_back=7)

    print()
    if success:
        print("✅ Price data updated successfully!")
        return 0
    else:
        print("❌ Price data collection failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
