import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FeatureProducer:
    """
    Standardized Feature Factory producing 50+ stationary features.
    """

    @staticmethod
    def produce_stationary_features(
        price_df: pd.DataFrame, sentiment_df: pd.DataFrame
    ) -> pd.DataFrame:
        # --- 1. Alignment & Gap Filling ---
        price_df["date"] = pd.to_datetime(price_df["date"])
        price_df = price_df.groupby(pd.Grouper(key="date", freq="1h")).first()
        full_range = pd.date_range(
            start=price_df.index.min(), end=price_df.index.max(), freq="1h"
        )
        df = price_df.reindex(full_range)

        df["close"] = df["close"].ffill()
        for col in ["open", "high", "low"]:
            df[col] = df[col].fillna(df["close"])
        df["volume"] = df["volume"].fillna(0)
        df["ticker"] = df["ticker"].ffill().fillna("BTC")

        # Merge Sentiment
        if sentiment_df is not None and not sentiment_df.empty:
            sentiment_df["date_h"] = pd.to_datetime(sentiment_df["date_h"])
            df = df.reset_index().rename(columns={"index": "date"})
            df = df.merge(sentiment_df, left_on="date", right_on="date_h", how="left")
            df["sentiment_avg"] = df["sentiment_avg"].fillna(0)
            df["news_count"] = df["news_count"].fillna(0)
        else:
            df = df.reset_index().rename(columns={"index": "date"})
            df["sentiment_avg"] = 0
            df["news_count"] = 0

        # --- 2. Advanced Feature Factory (50+ Features) ---

        # A. Price Returns (Multi-window)
        for w in [1, 2, 3, 6, 12, 24, 48, 72, 168]:
            df[f"feat_ret_log_{w}h"] = np.log(
                df["close"] / df["close"].shift(w)
            ).fillna(0)

        # B. Volatility (Multi-window std of returns)
        log_ret = np.log(df["close"] / df["close"].shift(1))
        for w in [6, 12, 24, 48, 168]:
            df[f"feat_volatility_{w}h"] = (
                log_ret.rolling(w, min_periods=1).std().fillna(0)
            )

        # C. Trend Distance (Relative乖離率)
        for w in [10, 20, 30, 50, 100, 200, 300, 500]:
            ma = df["close"].rolling(w, min_periods=1).mean()
            df[f"feat_ma_dist_{w}h"] = ((df["close"] - ma) / ma).fillna(0)

        # D. Relative High-Low Range
        for w in [1, 6, 12, 24, 48]:
            h_max = df["high"].rolling(w, min_periods=1).max()
            l_min = df["low"].rolling(w, min_periods=1).min()
            df[f"feat_hl_range_rel_{w}h"] = ((h_max - l_min) / df["close"]).fillna(0)

        # E. Relative Strength (RSI Multi-window)
        def get_rsi(s, n):
            d = s.diff()
            g = d.where(d > 0, 0).rolling(n, min_periods=1).mean()
            l = (-d.where(d < 0, 0)).rolling(n, min_periods=1).mean()
            return 100 - (100 / (1 + g / (l + 1e-9)))

        for w in [7, 14, 21, 28]:
            df[f"feat_rsi_{w}"] = get_rsi(df["close"], w).fillna(50)

        # F. Liquidity (Volume Z-Scores)
        for w in [12, 24, 48, 168]:
            v_m = df["volume"].rolling(w, min_periods=1).mean()
            v_s = df["volume"].rolling(w, min_periods=1).std().replace(0, 1)
            df[f"feat_vol_zscore_{w}h"] = ((df["volume"] - v_m) / v_s).fillna(0)

        # G. Sentiment Dynamics
        for w in [6, 12, 24, 48, 72, 168]:
            df[f"feat_sent_ma_{w}h"] = (
                df["sentiment_avg"].rolling(w, min_periods=1).mean().fillna(0)
            )
        for w in [1, 3, 6, 12, 24]:
            df[f"feat_sent_mom_{w}h"] = df["sentiment_avg"].diff(w).fillna(0)

        # H. Cyclical Time Features (Crucial for Hourly patterns)
        df["hour"] = df["date"].dt.hour
        df["dow"] = df["date"].dt.dayofweek
        df["feat_time_hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["feat_time_hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
        df["feat_time_dow_sin"] = np.sin(2 * np.pi * df["dow"] / 7)
        df["feat_time_dow_cos"] = np.cos(2 * np.pi * df["dow"] / 7)

        # I. Interaction Features (The "Alpha" features)
        df["feat_inter_sent_vol"] = df["feat_sent_ma_24h"] * df["feat_volatility_24h"]
        df["feat_inter_sent_rsi"] = (df["feat_sent_ma_24h"] / 100) * df["feat_rsi_14"]

        # --- 3. Target & Metadata ---
        df["target_return"] = log_ret.shift(-1)
        df["metadata_close"] = df["close"]

        # Selection
        feature_cols = [c for c in df.columns if c.startswith("feat_")]
        final_cols = [
            "date",
            "ticker",
            "target_return",
            "metadata_close",
        ] + feature_cols

        return df[final_cols].copy()
