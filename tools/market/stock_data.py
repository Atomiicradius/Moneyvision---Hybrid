"""
tools/market/stock_data.py
--------------------------
Phase 1 — Market Expert: Data Fetching

Provides clean, typed functions to pull stock data from yfinance.
All NSE symbols need the suffix '.NS', BSE symbols use '.BO'.

Why yfinance?
  - Free, no rate-limit registration needed for basic use
  - Returns pandas DataFrames — great for indicator calculations
  - Supports Indian exchanges natively via suffix convention
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Any, Optional

import yfinance as yf
import pandas as pd
import pytz

from core.config import MARKET_TIMEZONE, DEFAULT_CURRENCY
from core.logger import get_logger

logger = get_logger(__name__)
IST = pytz.timezone(MARKET_TIMEZONE)


def _validate_symbol(symbol: str) -> str:
    """
    Ensure the symbol has an exchange suffix.
    Raises ValueError with a helpful message if missing.
    """
    if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
        raise ValueError(
            f"Symbol '{symbol}' must end with '.NS' (NSE) or '.BO' (BSE). "
            f"Example: 'RELIANCE.NS'"
        )
    return symbol.upper()


def get_stock_price(symbol: str) -> Dict[str, Any]:
    """
    Fetch the latest price snapshot for a single Indian stock.

    Args:
        symbol: NSE/BSE ticker with suffix, e.g. "INFY.NS"

    Returns:
        Dict with keys: symbol, price, currency, market_cap,
                        pe_ratio, day_high, day_low, volume, fetched_at
    
    Raises:
        ValueError: If symbol format is wrong
        RuntimeError: If yfinance returns no data (market closed / invalid ticker)

    Example:
        >>> info = get_stock_price("TCS.NS")
        >>> print(info["price"])
    """
    symbol = _validate_symbol(symbol)
    logger.info(f"Fetching price snapshot for {symbol}")

    try:
        ticker = yf.Ticker(symbol)
        info   = ticker.info
    except Exception as e:
        raise RuntimeError(f"yfinance error for {symbol}: {e}") from e

    # 'regularMarketPrice' is None outside market hours; fall back to 'previousClose'
    price = (
        info.get("regularMarketPrice")
        or info.get("currentPrice")
        or info.get("previousClose")
    )

    if price is None:
        raise RuntimeError(
            f"No price data returned for '{symbol}'. "
            "Check the ticker symbol or try after market hours."
        )

    return {
        "symbol":     symbol,
        "price":      round(float(price), 2),
        "currency":   info.get("currency", DEFAULT_CURRENCY),
        "market_cap": info.get("marketCap"),
        "pe_ratio":   info.get("trailingPE"),
        "day_high":   info.get("dayHigh"),
        "day_low":    info.get("dayLow"),
        "volume":     info.get("volume"),
        "fetched_at": datetime.now(IST).isoformat(),
    }


def get_stock_history(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Download OHLCV historical data for a stock.

    Args:
        symbol:   NSE/BSE ticker, e.g. "HDFC.NS"
        period:   yfinance period string — "1mo", "3mo", "6mo", "1y", "2y"
        interval: Bar size — "1d", "1wk", "1mo"

    Returns:
        pandas DataFrame with columns: Open, High, Low, Close, Volume
        Index is DatetimeIndex (timezone-aware, IST)

    Why period strings instead of dates?
        Easier to use from UI sliders; yfinance handles the calendar math.
    """
    symbol = _validate_symbol(symbol)
    logger.info(f"Fetching history for {symbol} | period={period} interval={interval}")

    df = yf.download(symbol, period=period, interval=interval, progress=False)

    if df.empty:
        raise RuntimeError(
            f"No historical data for '{symbol}' with period='{period}'. "
            "The symbol may be delisted or the market may be on holiday."
        )

    # Flatten MultiIndex columns that yfinance sometimes returns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    logger.debug(f"Retrieved {len(df)} rows for {symbol}")
    return df


def is_market_open() -> bool:
    """
    Check if NSE/BSE is currently open (Mon–Fri, 09:15–15:30 IST).
    Does NOT account for market holidays (use NSEpy for that in Phase 3).

    Returns:
        True if within trading hours, False otherwise.
    """
    now = datetime.now(IST)
    if now.weekday() >= 5:          # Saturday=5, Sunday=6
        return False

    open_time  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return open_time <= now <= close_time
