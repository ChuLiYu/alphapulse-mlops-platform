import pandas as pd
import pandas_ta as ta

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    # Ensure timestamp is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # SMA
    df['sma_7'] = df.ta.sma(length=7)
    df['sma_25'] = df.ta.sma(length=25)
    df['sma_99'] = df.ta.sma(length=99)

    # EMA
    df['ema_12'] = df.ta.ema(length=12)
    df['ema_26'] = df.ta.ema(length=26)

    # RSI
    df['rsi_14'] = df.ta.rsi(length=14)

    # MACD
    macd = df.ta.macd(fast=12, slow=26, signal=9)
    if macd is not None:
        df = pd.concat([df, macd], axis=1)
        rename_map = {
            'MACD_12_26_9': 'macd',
            'MACDh_12_26_9': 'macd_histogram',
            'MACDs_12_26_9': 'macd_signal'
        }
        df.rename(columns=rename_map, inplace=True)

    # Bollinger Bands
    bb = df.ta.bbands(length=20, std=2)
    if bb is not None:
        df = pd.concat([df, bb], axis=1)
        rename_map_bb = {
            'BBL_20_2.0': 'bb_lower',
            'BBM_20_2.0': 'bb_middle',
            'BBU_20_2.0': 'bb_upper'
        }
        df.rename(columns=rename_map_bb, inplace=True)

    # ATR
    df['atr_14'] = df.ta.atr(length=14)

    # OBV
    df['obv'] = df.ta.obv()

    # ADX
    adx = df.ta.adx(length=14)
    if adx is not None:
        df = pd.concat([df, adx], axis=1)
        if 'ADX_14' in df.columns:
            df.rename(columns={'ADX_14': 'adx_14'}, inplace=True)

    df.fillna(0, inplace=True)
    return df
