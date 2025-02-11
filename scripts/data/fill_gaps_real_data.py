import requests
import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time

def fill_missing_gaps():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse")
    engine = create_engine(db_url)
    
    print("🔍 Scanning for gaps in btc_price_data...")
    df = pd.read_sql("SELECT date FROM btc_price_data ORDER BY date", engine)
    df['date'] = pd.to_datetime(df['date'])
    
    # 找出完整的理想時間軸
    full_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='1h')
    missing_dates = full_range.difference(df['date'])
    
    if len(missing_dates) == 0:
        print("✅ No gaps found! Data is already perfect.")
        return

    print(f"🚩 Found {len(missing_dates)} missing hours. Starting real-data backfill...")

    # Binance API
    url = "https://api.binance.com/api/v3/klines"
    
    added_count = 0
    # 為了效率，我們將連續的遺漏時間點組合成區塊來抓取
    # 但這裡採用的簡單邏輯是：如果遺漏，就抓取該點後的 1000 筆（會涵蓋後續的洞）
    
    i = 0
    while i < len(missing_dates):
        target_ts = int(missing_dates[i].timestamp() * 1000)
        print(f"   Fetching starting from: {missing_dates[i]}...")
        
        params = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "startTime": target_ts,
            "limit": 1000
        }
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if not data:
                i += 1
                continue
                
            new_rows = []
            for k in data:
                new_rows.append({
                    "date": pd.to_datetime(k[0], unit='ms'),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "ticker": "BTC",
                    "data_source": "Binance_Backfill"
                })
            
            # 寫入資料庫
            new_df = pd.DataFrame(new_rows)
            new_df['daily_return'] = new_df['close'].pct_change().fillna(0)
            new_df['log_return'] = np.log(new_df['close'] / new_df['close'].shift(1)).fillna(0)
            
            with engine.connect() as conn:
                new_df.to_sql("temp_fill", engine, if_exists="replace", index=False)
                conn.execute(text("""
                    INSERT INTO btc_price_data (date, open, high, low, close, volume, ticker, data_source, daily_return, log_return)
                    SELECT date, open, high, low, close, volume, ticker, data_source, daily_return, log_return FROM temp_fill
                    ON CONFLICT (date, ticker) DO NOTHING;
                """))
                conn.commit()
            
            added_count += len(new_rows)
            # 跳過已經填好的部分
            last_fetched = new_rows[-1]['date']
            while i < len(missing_dates) and missing_dates[i] <= last_fetched:
                i += 1
                
            time.sleep(0.2) # 禮貌性的頻率限制
            
        except Exception as e:
            print(f"⚠️ Error fetching at {missing_dates[i]}: {e}")
            i += 1
            time.sleep(2)

    print(f"🎉 Backfill complete! Added {added_count} real hourly records.")

if __name__ == "__main__":
    fill_missing_gaps()
