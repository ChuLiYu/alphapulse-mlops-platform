#!/usr/bin/env python3
"""
快速生成模型特徵數據
"""
import sys

sys.path.insert(0, "/app/src")

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text


def generate_features():
    """從價格數據生成特徵"""
    print("🔧 開始生成特徵...")

    engine = create_engine("postgresql://postgres:postgres@postgres:5432/alphapulse")

    try:
        # 加載價格數據
        with engine.connect() as conn:
            query = """
                SELECT 
                    timestamp as date,
                    symbol as ticker,
                    price as close,
                    volume
                FROM prices 
                WHERE symbol = 'BTC-USD'
                ORDER BY timestamp
            """
            df = pd.read_sql(query, conn.connection)

        print(f"✅ 加載了 {len(df)} 行價格數據")

        if len(df) < 50:
            print(f"❌ 數據不足: 只有 {len(df)} 行")
            return False

        # 添加基本特徵
        print("📊 計算技術指標...")

        # 價格變化
        df["price_change_1d"] = df["close"].pct_change()
        df["price_change_3d"] = df["close"].pct_change(3)
        df["price_change_7d"] = df["close"].pct_change(7)
        df["price_change_14d"] = df["close"].pct_change(14)

        # 成交量變化
        df["volume_change_1d"] = df["volume"].pct_change()
        df["volume_change_7d"] = df["volume"].pct_change(7)

        # 移動平均
        df["sma_7"] = df["close"].rolling(7).mean()
        df["sma_20"] = df["close"].rolling(20).mean()
        df["sma_50"] = df["close"].rolling(50).mean()

        # EMA
        df["ema_7"] = df["close"].ewm(span=7).mean()
        df["ema_20"] = df["close"].ewm(span=20).mean()

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # 布林帶
        bb_period = 20
        bb_std = 2
        df["bb_middle"] = df["close"].rolling(bb_period).mean()
        bb_std_val = df["close"].rolling(bb_period).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * bb_std_val)
        df["bb_lower"] = df["bb_middle"] - (bb_std * bb_std_val)
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"] + 1e-10
        )

        # MACD
        ema_12 = df["close"].ewm(span=12).mean()
        ema_26 = df["close"].ewm(span=26).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # 波動率
        df["volatility_7d"] = df["close"].pct_change().rolling(7).std()
        df["volatility_20d"] = df["close"].pct_change().rolling(20).std()
        df["volatility_50d"] = df["close"].pct_change().rolling(50).std()

        # 動量指標
        df["momentum_7d"] = df["close"] - df["close"].shift(7)
        df["momentum_14d"] = df["close"] - df["close"].shift(14)

        # ROC (Rate of Change)
        df["roc_7d"] = (
            (df["close"] - df["close"].shift(7)) / (df["close"].shift(7) + 1e-10)
        ) * 100
        df["roc_14d"] = (
            (df["close"] - df["close"].shift(14)) / (df["close"].shift(14) + 1e-10)
        ) * 100

        # 最高/最低價
        df["high_7d"] = df["close"].rolling(7).max()
        df["low_7d"] = df["close"].rolling(7).min()
        df["high_20d"] = df["close"].rolling(20).max()
        df["low_20d"] = df["close"].rolling(20).min()

        # 價格位置
        df["price_position_7d"] = (df["close"] - df["low_7d"]) / (
            df["high_7d"] - df["low_7d"] + 1e-10
        )
        df["price_position_20d"] = (df["close"] - df["low_20d"]) / (
            df["high_20d"] - df["low_20d"] + 1e-10
        )

        # 時間特徵
        df["date"] = pd.to_datetime(df["date"])
        df["day_of_week"] = df["date"].dt.dayofweek
        df["day_of_month"] = df["date"].dt.day
        df["month"] = df["date"].dt.month
        df["quarter"] = df["date"].dt.quarter

        # 填充缺失值
        print("🔧 處理缺失值...")
        df = df.fillna(method="bfill").fillna(method="ffill").fillna(0)

        # 只保留有完整數據的行（去掉前面的NaN）
        df = df.iloc[50:]  # 跳過前50行（需要用於計算移動平均）

        print(f"✅ 生成了 {len(df)} 行特徵，{len(df.columns)} 個特徵列")

        if len(df) > 100:
            # 保存到數據庫
            print("💾 保存到 model_features 表...")
            with engine.begin() as conn:
                df.to_sql("model_features", conn, if_exists="replace", index=False)
            print(f"✅ 成功保存 {len(df)} 行特徵數據")

            # 顯示特徵列
            print(f"\n📋 特徵列 ({len(df.columns)}):")
            for col in df.columns:
                print(f"  - {col}")

            return True
        else:
            print(f"❌ 數據不足，只有 {len(df)} 行")
            return False

    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = generate_features()
    sys.exit(0 if success else 1)
