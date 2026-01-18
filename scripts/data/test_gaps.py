import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine


def debug_gaps():
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse"
    )
    engine = create_engine(db_url)

    df = pd.read_sql("SELECT date, close FROM btc_price_data ORDER BY date", engine)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    print(f"Original range: {df.index.min()} to {df.index.max()}")
    print(f"Original rows: {len(df)}")

    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="1h")
    print(f"Expected hourly rows: {len(full_range)}")

    df_reindexed = df.reindex(full_range)
    print(f"Reindexed NaNs: {df_reindexed['close'].isna().sum()}")

    df_filled = df_reindexed.ffill()
    print(f"Filled NaNs remaining: {df_filled['close'].isna().sum()}")

    # Calculate MA 200
    df_filled["ma200"] = df_filled["close"].rolling(200).mean()
    print(f"MA200 NaNs: {df_filled['ma200'].isna().sum()}")

    # Dropna result
    df_final = df_filled.dropna()
    print(f"Final rows after dropna: {len(df_final)}")


if __name__ == "__main__":
    debug_gaps()
