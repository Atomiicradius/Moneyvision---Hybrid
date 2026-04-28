"""
tools/market/indicators.py
---------------------------
Phase 1 — Market Expert: Technical Indicators

Why calculate indicators ourselves (not use TA-Lib)?
  - TA-Lib has complex C-dependency installs on Windows
  - Rolling pandas operations are transparent and educational
  - Easy to unit-test without binary dependencies

All functions accept a pd.DataFrame from get_stock_history()
and return a new DataFrame with the indicator column(s) appended.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from core.logger import get_logger

logger = get_logger(__name__)


def calc_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    Relative Strength Index (RSI) — Momentum Oscillator.

    Financial Principle:
        RSI measures the speed and magnitude of price changes.
        - RSI > 70  → Overbought (potential sell signal)
        - RSI < 30  → Oversold  (potential buy signal)

    Math:
        RS  = Average Gain over N periods / Average Loss over N periods
        RSI = 100 - (100 / (1 + RS))

    Args:
        df:     OHLCV DataFrame (must contain 'Close' column)
        window: Look-back period (default 14 — Wilder's original)

    Returns:
        DataFrame with new column 'RSI'
    """
    if "Close" not in df.columns:
        raise KeyError("DataFrame must have a 'Close' column.")

    delta   = df["Close"].diff()
    gain    = delta.clip(lower=0)
    loss    = (-delta).clip(lower=0)

    # Wilder's smoothing (exponential moving average with alpha = 1/window)
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()

    rs  = avg_gain / avg_loss.replace(0, np.nan)   # avoid division by zero
    rsi = 100 - (100 / (1 + rs))

    df = df.copy()
    df["RSI"] = rsi.round(2)
    logger.debug(f"RSI({window}) calculated. Latest: {df['RSI'].iloc[-1]:.2f}")
    return df


def calc_moving_averages(
    df: pd.DataFrame,
    windows: list[int] = [20, 50, 200],
) -> pd.DataFrame:
    """
    Simple Moving Averages (SMA) for multiple windows.

    Financial Principle:
        - Price > MA_50 while MA_50 > MA_200 → Bullish trend
        - Price crosses below MA_50           → Short-term weakness
        - MA_20 crossing MA_50 upward         → "Golden Cross" (strong buy signal)

    Args:
        df:      OHLCV DataFrame
        windows: List of look-back periods (default: 20, 50, 200)

    Returns:
        DataFrame with new columns 'MA_20', 'MA_50', 'MA_200' (etc.)
    """
    df = df.copy()
    for w in windows:
        col = f"MA_{w}"
        df[col] = df["Close"].rolling(window=w).mean().round(2)
        logger.debug(f"{col} calculated. Latest: {df[col].iloc[-1]:.2f}")
    return df


def calc_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Historical Volatility — Annualised Standard Deviation of Returns.

    Financial Principle:
        Volatility = StdDev of daily log returns × √252
        (252 = trading days in a year for NSE/BSE)

        Higher volatility → higher risk → potentially higher return.
        Use this to set stop-losses and position sizing.

    Args:
        df:     OHLCV DataFrame
        window: Rolling window for StdDev (default 20 days ≈ 1 trading month)

    Returns:
        DataFrame with new column 'Volatility' (annualised, as a fraction)
        e.g. 0.25 means 25% annualised volatility
    """
    df = df.copy()
    log_returns     = np.log(df["Close"] / df["Close"].shift(1))
    df["Volatility"] = (
        log_returns.rolling(window=window).std() * np.sqrt(252)
    ).round(4)
    logger.debug(f"Volatility({window}) calculated. Latest: {df['Volatility'].iloc[-1]:.4f}")
    return df


def get_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience wrapper: apply RSI + Moving Averages + Volatility in one call.

    Returns:
        DataFrame with columns: RSI, MA_20, MA_50, MA_200, Volatility
    """
    df = calc_rsi(df)
    df = calc_moving_averages(df, windows=[20, 50, 200])
    df = calc_volatility(df)
    return df
