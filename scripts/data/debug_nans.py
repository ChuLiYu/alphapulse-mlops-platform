import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine

def debug_nans():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse")
    engine = create_engine(db_url)
    
    price_df = pd.read_sql("SELECT date, close, volume FROM btc_price_data ORDER BY date", engine)
    price_df['date'] = pd.to_datetime(price_df['date'])
    
    # Simple Deduplicate
    df = price_df.groupby(pd.Grouper(key='date', freq='1h')).first().reset_index()
    
    # Features
    df['feat_returns_log'] = np.log(df['close'] / df['close'].shift(1))
    for w in [50, 200]:
        ma = df['close'].rolling(window=w).mean()
        df[f'feat_ma_dist_{w}'] = (df['close'] - ma) / ma
    
    vol_rolling = df['volume'].rolling(window=24)
    df['feat_volume_zscore'] = (df['volume'] - vol_rolling.mean()) / vol_rolling.std()
    df['target_return'] = df['feat_returns_log'].shift(-1)
    
    print("--- NaN Count Per Column ---")
    print(df.isna().sum())
    
    print("\n--- Inf Count Per Column ---")
    print(np.isinf(df.select_dtypes(include=[np.number])).sum())
    
    # Try dropna
    df_clean = df.dropna()
    print(f"\nRows before dropna: {len(df)}")
    print(f"Rows after dropna: {len(df_clean)}")

if __name__ == "__main__":
    debug_nans()
