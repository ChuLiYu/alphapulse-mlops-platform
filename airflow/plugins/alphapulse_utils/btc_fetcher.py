import pandas as pd
import yfinance as yf
import requests
import time
from datetime import datetime, timedelta


def fetch_from_coingecko(start_date, end_date):
    print("📊 Trying CoinGecko API...")
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # days_diff = (end_dt - start_dt).days
    # if days_diff > 365:
    #     start_dt = end_dt - timedelta(days=365)

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
    params = {"vs_currency": "usd", "from": start_ts, "to": end_ts}

    response = requests.get(url, params=params, timeout=30)
    if response.status_code != 200:
        raise Exception(f"CoinGecko API Error: {response.status_code}")

    data = response.json()
    prices = data.get("prices", [])
    total_volumes = data.get("total_volumes", [])

    if not prices:
        raise Exception("No price data from CoinGecko")

    df = pd.DataFrame(prices, columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    df_vol = pd.DataFrame(total_volumes, columns=["timestamp", "volume"])
    df_vol["timestamp"] = pd.to_datetime(df_vol["timestamp"], unit="ms")

    df = df.merge(df_vol, on="timestamp", how="left")
    df["open"] = df["close"]
    df["high"] = df["close"]
    df["low"] = df["close"]

    df.set_index("timestamp", inplace=True)
    df_daily = (
        df.resample("D")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
        .reset_index()
    )

    return df_daily


def fetch_from_yfinance(
    symbol="BTC-USD", start_date="2020-01-01", end_date=None, max_retries=3
):
    print("📊 Trying Yahoo Finance...")
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    for attempt in range(max_retries):
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df.reset_index(inplace=True)
                df.columns = [c.lower().replace(" ", "_") for c in df.columns]
                if "date" in df.columns:
                    df.rename(columns={"date": "timestamp"}, inplace=True)
                return df
        except Exception as e:
            print(f"YFinance attempt {attempt+1} failed: {e}")
            time.sleep(2)

    raise Exception("Yahoo Finance failed")


def load_btc_data():
    """
    Main function to fetch BTC data from multiple sources.
    """
    start_date = "2020-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        return fetch_from_yfinance(start_date=start_date, end_date=end_date)
    except Exception as e:
        print(f"YFinance failed: {e}. Trying CoinGecko...")
        try:
            return fetch_from_coingecko(start_date, end_date)
        except Exception as e2:
            raise Exception(f"All sources failed. YF: {e}, CG: {e2}")
