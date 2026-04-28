"""
tests/test_market.py
---------------------
Unit tests for the Market Expert tools.

Run with:
    pytest tests/ -v

These tests use real yfinance calls for a well-known stable stock (TCS.NS).
If you're offline, mock with pytest-mock.
"""

import pytest
import pandas as pd

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.market.stock_data import get_stock_price, get_stock_history, is_market_open
from tools.market.indicators import calc_rsi, calc_moving_averages, calc_volatility


# ── stock_data ────────────────────────────────────────────────────────────────

def test_get_stock_price_valid():
    result = get_stock_price("TCS.NS")
    assert "price" in result
    assert result["price"] > 0
    assert result["symbol"] == "TCS.NS"

def test_get_stock_price_invalid_symbol():
    with pytest.raises(ValueError, match="must end with"):
        get_stock_price("TCS")   # Missing exchange suffix

def test_get_stock_history_returns_dataframe():
    df = get_stock_history("INFY.NS", period="1mo")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Close" in df.columns

def test_is_market_open_returns_bool():
    result = is_market_open()
    assert isinstance(result, bool)


# ── indicators ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    """Provide a 60-row history DataFrame for indicator tests."""
    return get_stock_history("RELIANCE.NS", period="3mo")

def test_rsi_column_added(sample_df):
    df = calc_rsi(sample_df)
    assert "RSI" in df.columns

def test_rsi_values_in_range(sample_df):
    df = calc_rsi(sample_df)
    valid = df["RSI"].dropna()
    assert (valid >= 0).all() and (valid <= 100).all()

def test_moving_averages_added(sample_df):
    df = calc_moving_averages(sample_df, windows=[20, 50])
    assert "MA_20" in df.columns
    assert "MA_50" in df.columns

def test_volatility_positive(sample_df):
    df = calc_volatility(sample_df)
    assert "Volatility" in df.columns
    assert df["Volatility"].dropna().gt(0).all()
