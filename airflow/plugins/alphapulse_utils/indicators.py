"""
Technical indicators — pure pandas / numpy implementation.
Zero external TA library dependencies.

Replaces pandas_ta to permanently eliminate numpy version conflicts
with the Airflow base image.

All formulas follow standard financial definitions:
  https://school.stockcharts.com/doku.php?id=technical_indicators

Usage (drop-in replacement for pandas_ta calls):
    from alphapulse_utils.indicators import sma, ema, rsi, macd, bbands, atr, obv, adx

Author note for interviews:
    Every indicator here is implemented from first principles using
    pandas rolling windows and ewm (exponentially weighted mean).
    This ensures full control over precision and zero external dependencies.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────


def _validate(series: pd.Series, name: str = "series") -> None:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series, got {type(series)}")


def _validate_ohlcv(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series | None = None,
) -> None:
    for s, n in [(high, "high"), (low, "low"), (close, "close")]:
        _validate(s, n)
    if volume is not None:
        _validate(volume, "volume")


# ─────────────────────────────────────────────────────────────────────────────
# 1. SMA — Simple Moving Average
# ─────────────────────────────────────────────────────────────────────────────


def sma(series: pd.Series, period: int) -> pd.Series:
    """
    Simple Moving Average.

    Formula:
        SMA(t) = mean(close[t-period+1 : t+1])

    Args:
        series: Price series (typically close).
        period: Lookback window length.

    Returns:
        pd.Series aligned with input index, NaN for first (period-1) rows.
    """
    _validate(series, "series")
    return (
        series.rolling(window=period, min_periods=period).mean().rename(f"SMA_{period}")
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. EMA — Exponential Moving Average
# ─────────────────────────────────────────────────────────────────────────────


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average.

    Formula:
        alpha = 2 / (period + 1)
        EMA(t) = alpha * close(t) + (1 - alpha) * EMA(t-1)

    Uses pandas ewm with adjust=False (recursive/Wilder-style).

    Args:
        series: Price series.
        period: Span for the exponential decay (equivalent to N-period EMA).

    Returns:
        pd.Series aligned with input index.
    """
    _validate(series, "series")
    return (
        series.ewm(span=period, adjust=False, min_periods=period)
        .mean()
        .rename(f"EMA_{period}")
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. RSI — Relative Strength Index
# ─────────────────────────────────────────────────────────────────────────────


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (Wilder, 1978).

    Formula:
        delta   = close.diff()
        gain    = delta.clip(lower=0)
        loss    = (-delta).clip(lower=0)
        avg_gain = EWM(gain, alpha=1/period)   # Wilder smoothing
        avg_loss = EWM(loss, alpha=1/period)
        RS      = avg_gain / avg_loss
        RSI     = 100 - (100 / (1 + RS))

    Wilder's smoothing uses alpha = 1/period, equivalent to
    a (2*period - 1)-period EMA.

    Args:
        series: Close price series.
        period: Lookback period (default 14).

    Returns:
        pd.Series of RSI values in range [0, 100].
    """
    _validate(series, "series")
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    # Wilder smoothing: alpha = 1/period
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100.0 - (100.0 / (1.0 + rs))

    # Edge: avg_loss == 0 means pure uptrend → RSI = 100
    rsi_series = rsi_series.where(avg_loss != 0, other=100.0)

    return rsi_series.rename(f"RSI_{period}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. MACD — Moving Average Convergence Divergence
# ─────────────────────────────────────────────────────────────────────────────


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    MACD (Gerald Appel, 1979).

    Formula:
        MACD Line   = EMA(fast) - EMA(slow)
        Signal Line = EMA(MACD Line, signal)
        Histogram   = MACD Line - Signal Line

    Args:
        series: Close price series.
        fast:   Fast EMA period (default 12).
        slow:   Slow EMA period (default 26).
        signal: Signal line EMA period (default 9).

    Returns:
        pd.DataFrame with columns:
            MACD_{fast}_{slow}_{signal}         — MACD line
            MACDs_{fast}_{slow}_{signal}        — Signal line
            MACDh_{fast}_{slow}_{signal}        — Histogram
    """
    _validate(series, "series")
    suffix = f"{fast}_{slow}_{signal}"

    ema_fast = series.ewm(span=fast, adjust=False, min_periods=fast).mean()
    ema_slow = series.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd_line = ema_fast - ema_slow
    sig_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    histogram = macd_line - sig_line

    return pd.DataFrame(
        {
            f"MACD_{suffix}": macd_line,
            f"MACDs_{suffix}": sig_line,
            f"MACDh_{suffix}": histogram,
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Bollinger Bands
# ─────────────────────────────────────────────────────────────────────────────


def bbands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> pd.DataFrame:
    """
    Bollinger Bands (John Bollinger, 1983).

    Formula:
        Middle Band = SMA(period)
        Upper Band  = Middle + std_dev * rolling_std(period)
        Lower Band  = Middle - std_dev * rolling_std(period)
        Bandwidth   = (Upper - Lower) / Middle
        %B          = (close - Lower) / (Upper - Lower)

    Args:
        series:  Close price series.
        period:  Rolling window (default 20).
        std_dev: Number of standard deviations (default 2.0).

    Returns:
        pd.DataFrame with columns:
            BBL_{period}_{std_dev}  — Lower band
            BBM_{period}_{std_dev}  — Middle band (SMA)
            BBU_{period}_{std_dev}  — Upper band
            BBB_{period}_{std_dev}  — Bandwidth
            BBP_{period}_{std_dev}  — %B
    """
    _validate(series, "series")
    suffix = f"{period}_{std_dev}"

    rolling = series.rolling(window=period, min_periods=period)
    middle = rolling.mean()
    std = rolling.std(ddof=0)  # population std, matches TradingView default

    upper = middle + std_dev * std
    lower = middle - std_dev * std
    bw = (upper - lower) / middle.replace(0, np.nan)
    pct_b = (series - lower) / (upper - lower).replace(0, np.nan)

    return pd.DataFrame(
        {
            f"BBL_{suffix}": lower,
            f"BBM_{suffix}": middle,
            f"BBU_{suffix}": upper,
            f"BBB_{suffix}": bw,
            f"BBP_{suffix}": pct_b,
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6. ATR — Average True Range
# ─────────────────────────────────────────────────────────────────────────────


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    Average True Range (Wilder, 1978).

    True Range = max(
        high - low,
        |high - prev_close|,
        |low  - prev_close|
    )
    ATR = Wilder EMA(True Range, period)
        = EWM(TR, alpha=1/period)

    Args:
        high:   High price series.
        low:    Low price series.
        close:  Close price series.
        period: Lookback period (default 14).

    Returns:
        pd.Series of ATR values.
    """
    _validate_ohlcv(high, low, close)
    prev_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr_series = tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    return atr_series.rename(f"ATRr_{period}")


# ─────────────────────────────────────────────────────────────────────────────
# 7. OBV — On-Balance Volume
# ─────────────────────────────────────────────────────────────────────────────


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    On-Balance Volume (Joseph Granville, 1963).

    Formula:
        If close > prev_close: OBV = prev_OBV + volume
        If close < prev_close: OBV = prev_OBV - volume
        If close == prev_close: OBV = prev_OBV

    This is a pure cumulative sum — no rolling window, no smoothing.

    Args:
        close:  Close price series.
        volume: Volume series.

    Returns:
        pd.Series of OBV values (cumulative).
    """
    _validate(close, "close")
    _validate(volume, "volume")

    direction = np.sign(close.diff()).fillna(0)
    obv_series = (direction * volume).cumsum()
    return obv_series.rename("OBV")


# ─────────────────────────────────────────────────────────────────────────────
# 8. ADX — Average Directional Index
# ─────────────────────────────────────────────────────────────────────────────


def adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.DataFrame:
    """
    Average Directional Index (Wilder, 1978).

    Steps:
        1. True Range (TR) — same as ATR
        2. +DM = high - prev_high  if positive and > |low - prev_low|, else 0
           -DM = prev_low - low    if positive and > |high - prev_high|, else 0
        3. Smooth TR, +DM, -DM using Wilder EMA (alpha=1/period)
        4. +DI = 100 * smooth(+DM) / smooth(TR)
           -DI = 100 * smooth(-DM) / smooth(TR)
        5. DX  = 100 * |+DI - -DI| / (+DI + -DI)
        6. ADX = Wilder EMA(DX, period)

    ADX > 25 generally indicates a trending market.
    ADX < 20 indicates a ranging / non-trending market.

    Args:
        high:   High price series.
        low:    Low price series.
        close:  Close price series.
        period: Lookback period (default 14).

    Returns:
        pd.DataFrame with columns:
            ADX_{period}   — Average Directional Index
            DMP_{period}   — +DI (positive directional indicator)
            DMN_{period}   — -DI (negative directional indicator)
    """
    _validate_ohlcv(high, low, close)

    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    # True Range
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    # Directional Movement
    up_move = high - prev_high
    down_move = prev_low - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm_s = pd.Series(plus_dm, index=high.index)
    minus_dm_s = pd.Series(minus_dm, index=high.index)

    # Wilder smoothing (alpha = 1/period)
    alpha = 1.0 / period
    smooth_tr = tr.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    smooth_plus_dm = plus_dm_s.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    smooth_minus_dm = minus_dm_s.ewm(
        alpha=alpha, adjust=False, min_periods=period
    ).mean()

    # Directional Indicators
    plus_di = 100.0 * smooth_plus_dm / smooth_tr.replace(0, np.nan)
    minus_di = 100.0 * smooth_minus_dm / smooth_tr.replace(0, np.nan)

    # DX and ADX
    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / di_sum
    adx_val = dx.ewm(alpha=alpha, adjust=False, min_periods=period).mean()

    return pd.DataFrame(
        {
            f"ADX_{period}": adx_val,
            f"DMP_{period}": plus_di,
            f"DMN_{period}": minus_di,
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Backward-compatible wrapper (drop-in replacement for pandas_ta usage)
# ─────────────────────────────────────────────────────────────────────────────


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators using pure pandas/numpy implementation.

    Drop-in replacement for the old pandas_ta-based calculate_indicators function.
    Returns DataFrame with same column names as before.

    Required columns: high, low, close, volume (case-insensitive)
    Optional: timestamp

    Returns DataFrame with columns:
        - sma_7, sma_25, sma_99
        - ema_12, ema_26
        - rsi_14
        - macd, macd_histogram, macd_signal
        - bb_lower, bb_middle, bb_upper (or BBL_20_2.0, BBM_20_2.0, BBU_20_2.0)
        - atr_14
        - obv
        - adx_14
    """
    if df is None or df.empty:
        return df

    # Normalize column names to lowercase
    col_map = {c.lower(): c for c in df.columns}

    # Check for required columns
    required = ["close", "high", "low", "volume"]
    for col in required:
        if col not in col_map:
            raise ValueError(f"Missing required column: {col}")

    close = df[col_map["close"]]
    high = df[col_map["high"]]
    low = df[col_map["low"]]
    volume = df[col_map["volume"]]

    result = df.copy()

    # Ensure timestamp is datetime if present
    if "timestamp" in col_map:
        result.loc[:, col_map["timestamp"]] = pd.to_datetime(
            result[col_map["timestamp"]]
        )

    # ── SMA ───────────────────────────────────────────────────────────────
    result["sma_7"] = sma(close, 7)
    result["sma_25"] = sma(close, 25)
    result["sma_99"] = sma(close, 99)

    # ── EMA ───────────────────────────────────────────────────────────────
    result["ema_12"] = ema(close, 12)
    result["ema_26"] = ema(close, 26)

    # ── RSI ───────────────────────────────────────────────────────────────
    result["rsi_14"] = rsi(close, 14)

    # ── MACD ─────────────────────────────────────────────────────────────
    macd_df = macd(close, fast=12, slow=26, signal=9)
    result["macd"] = macd_df["MACD_12_26_9"]
    result["macd_histogram"] = macd_df["MACDh_12_26_9"]
    result["macd_signal"] = macd_df["MACDs_12_26_9"]

    # ── Bollinger Bands ────────────────────────────────────────────────
    bb_df = bbands(close, period=20, std_dev=2.0)
    result["bb_lower"] = bb_df["BBL_20_2.0"]
    result["bb_middle"] = bb_df["BBM_20_2.0"]
    result["bb_upper"] = bb_df["BBU_20_2.0"]

    # ── ATR ─────────────────────────────────────────────────────────────
    result["atr_14"] = atr(high, low, close, period=14)

    # ── OBV ─────────────────────────────────────────────────────────────
    result["obv"] = obv(close, volume)

    # ── ADX ─────────────────────────────────────────────────────────────
    adx_df = adx(high, low, close, period=14)
    result["adx_14"] = adx_df["ADX_14"]

    # Fill NaN values
    result.fillna(0, inplace=True)

    return result
