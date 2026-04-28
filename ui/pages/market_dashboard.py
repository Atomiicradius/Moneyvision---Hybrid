"""
ui/pages/market_dashboard.py
------------------------------
Streamlit page: Market Intelligence Dashboard

Displays live price, RSI, moving averages, volatility chart,
and a plain-English signal summary for any NSE/BSE stock.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Add project root to path so tools/ and core/ are importable
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from tools.market.stock_data import get_stock_price, get_stock_history, is_market_open
from tools.market.indicators import get_all_indicators

#DISCLAIMER = "⚠️ *This is for educational analysis, not certified financial advice.*"

POPULAR_STOCKS = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS":                 "TCS.NS",
    "Infosys":             "INFY.NS",
    "HDFC Bank":           "HDFCBANK.NS",
    "ICICI Bank":          "ICICIBANK.NS",
    "Wipro":               "WIPRO.NS",
    "SBI":                 "SBIN.NS",
    "Bajaj Finance":       "BAJFINANCE.NS",
}


def render():
    st.title("📈 Market Intelligence Dashboard")
    st.caption(DISCLAIMER)

    # ── Market Status Badge ────────────────────────────────────────────────────
    open_flag = is_market_open()
    badge = "🟢 Market Open (NSE/BSE)" if open_flag else "🔴 Market Closed"
    st.markdown(f"**{badge}**")
    st.divider()

    # ── Stock Selector ─────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])
    with col1:
        preset = st.selectbox("Quick Select", ["Custom…"] + list(POPULAR_STOCKS.keys()))
    with col2:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)

    if preset == "Custom…":
        symbol = st.text_input(
            "Enter NSE/BSE Symbol",
            placeholder="e.g. TATAMOTORS.NS",
            help="Use suffix .NS for NSE, .BO for BSE",
        ).strip().upper()
    else:
        symbol = POPULAR_STOCKS[preset]
        st.info(f"Using symbol: **{symbol}**")

    if not symbol:
        st.info("Enter or select a stock symbol above to begin.")
        return

    # ── Fetch Data ─────────────────────────────────────────────────────────────
    with st.spinner(f"Fetching data for {symbol}…"):
        try:
            price_info = get_stock_price(symbol)
            df_raw     = get_stock_history(symbol, period=period)
            df         = get_all_indicators(df_raw)
        except (ValueError, RuntimeError) as e:
            st.error(str(e))
            return

    # ── Price Metric Cards ─────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Price",  f"₹{price_info['price']:,.2f}")
    c2.metric("Day High",       f"₹{price_info['day_high']:,.2f}" if price_info['day_high'] else "—")
    c3.metric("Day Low",        f"₹{price_info['day_low']:,.2f}"  if price_info['day_low']  else "—")
    c4.metric("Volume",         f"{price_info['volume']:,}"        if price_info['volume']   else "—")

    pe = price_info.get("pe_ratio")
    mc = price_info.get("market_cap")
    if pe or mc:
        ca, cb = st.columns(2)
        if pe:  ca.metric("P/E Ratio",    f"{pe:.1f}")
        if mc:  cb.metric("Market Cap",   f"₹{mc/1e7:,.0f} Cr")

    st.divider()

    # ── Candlestick + Volume Chart ─────────────────────────────────────────────
    st.subheader("Price Chart")

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.2, 0.25],
        vertical_spacing=0.04,
        subplot_titles=("OHLC + Moving Averages", "Volume", "RSI (14)"),
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="OHLC",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ), row=1, col=1)

    # Moving Averages
    for ma, color in [("MA_20", "#FFD700"), ("MA_50", "#00BFFF"), ("MA_200", "#FF8C00")]:
        if ma in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ma], name=ma,
                line=dict(color=color, width=1.5),
            ), row=1, col=1)

    # Volume bars
    colors = ["#26a69a" if c >= o else "#ef5350"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        name="Volume", marker_color=colors, opacity=0.7,
    ), row=2, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"],
        name="RSI", line=dict(color="#AB47BC", width=2),
    ), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red",   row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.update_layout(
        height=700,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Signal Summary ─────────────────────────────────────────────────────────
    st.subheader("📊 Signal Summary")
    latest = df.iloc[-1]

    signals = []
    rsi_val = latest.get("RSI")
    if pd.notna(rsi_val):
        if rsi_val > 70:
            signals.append(("🔴 RSI Overbought", f"RSI = {rsi_val:.1f} — Momentum may be stretched. Possible pullback ahead."))
        elif rsi_val < 30:
            signals.append(("🟢 RSI Oversold",   f"RSI = {rsi_val:.1f} — Stock may be undervalued relative to recent momentum."))
        else:
            signals.append(("⚪ RSI Neutral",    f"RSI = {rsi_val:.1f} — No extreme momentum signal."))

    ma20, ma50 = latest.get("MA_20"), latest.get("MA_50")
    close = latest["Close"]
    if pd.notna(ma20) and pd.notna(ma50):
        if close > ma50:
            signals.append(("🟢 Above MA_50", "Price is above 50-day MA — short-term bullish bias."))
        else:
            signals.append(("🔴 Below MA_50", "Price is below 50-day MA — short-term bearish bias."))
        if ma20 > ma50:
            signals.append(("🟢 Golden Cross (MA_20 > MA_50)", "Short-term average above medium-term — bullish trend structure."))
        else:
            signals.append(("🔴 Death Cross (MA_20 < MA_50)",  "Short-term average below medium-term — bearish trend structure."))

    vol = latest.get("Volatility")
    if pd.notna(vol):
        signals.append(("📉 Volatility", f"Annualised volatility = {vol:.1%} — {'High risk' if vol > 0.4 else 'Moderate risk' if vol > 0.2 else 'Low risk'}."))

    for title, desc in signals:
        with st.expander(title, expanded=True):
            st.write(desc)

    st.caption(DISCLAIMER)
