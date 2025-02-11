import requests
import pandas as pd
import os
from sqlalchemy import create_engine, text
from datetime import datetime
import time
import numpy as np

def fetch_hourly_from_binance():
    print("🚀 Fetching real historical HOURLY (1h) BTC-USDT data from Binance...")
    url = "https://api.binance.com/api/v3/klines"
    
    all_klines = []
    # Start from Aug 17, 2017 (Binance launch) or Jan 1, 2018 for cleaner data
    start_ts = int(datetime(2018, 1, 1).timestamp() * 1000)
    end_ts = int(datetime.now().timestamp() * 1000)
    
    current_start = start_ts
    while current_start < end_ts:
        params = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "startTime": current_start,
            "limit": 1000
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if not data or len(data) == 0:
                break
                
            all_klines.extend(data)
            # Move start to the next candle (1h = 3600000 ms)
            current_start = data[-1][0] + 3600000 
            
            if len(all_klines) % 5000 == 0 or len(data) < 1000:
                print(f"   Collected {len(all_klines)} hours...")
            
            time.sleep(0.1) # Faster but safe
        except Exception as e:
            print(f"Error: {e}. Retrying in 2s...")
            time.sleep(2)
            continue
        
    df = pd.DataFrame(all_klines)
    df = df[[0, 1, 2, 3, 4, 5]]
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    # Convert types
    df['date'] = pd.to_datetime(df['date'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
        
    df['ticker'] = 'BTC'
    df['data_source'] = 'Binance_1h'
    
    # Calculate Hourly Returns
    df['daily_return'] = df['close'].pct_change() # Named 'daily_return' for schema compatibility
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    return df.dropna()

def backfill_hourly_prices():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse")
    engine = create_engine(db_url)
    
    df = fetch_hourly_from_binance()
    
    print(f"✅ Processed {len(df)} hours of real price data.")
    
    with engine.connect() as conn:
        # We replace the table for hourly data as it's a major schema/granularity shift
        # Actually, UPSERT is safer if we want to keep current data
        df.to_sql("temp_prices_hourly", engine, if_exists="replace", index=False)
        
        upsert_query = text("""
            INSERT INTO btc_price_data (date, ticker, open, high, low, close, volume, daily_return, log_return, data_source)
            SELECT date, ticker, open, high, low, close, volume, daily_return, log_return, data_source
            FROM temp_prices_hourly
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
        conn.execute(text("DROP TABLE temp_prices_hourly;"))
        conn.commit()
        
    print(f"🎉 Successfully backfilled {len(df)} hours of real BTC price data!")

if __name__ == "__main__":
    backfill_hourly_prices()
