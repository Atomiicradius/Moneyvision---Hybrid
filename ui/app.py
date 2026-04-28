"""
ui/app.py
----------
FinIntel Hybrid — Main Streamlit Entry Point

Run with:
    streamlit run ui/app.py

Navigation is handled via st.navigation (Streamlit 1.36+).
Each page is a separate module in ui/pages/.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

# Page imports
from ui.pages import market_dashboard, expense_tracker

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinIntel Hybrid",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark sidebar gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    }
    /* Metric cards */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    /* Headers */
    h1 { color: #7EB8F7; }
    h2 { color: #A8D8A8; }
    /* Primary button accent */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #667eea, #764ba2);
        border: none;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💹 FinIntel Hybrid")
    st.caption("AI-Powered Financial Intelligence")
    st.divider()
    page = st.radio(
        "Navigate",
        options=["📈 Market Dashboard", "💸 Expense Tracker"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(
        "📌 **Phase 1** — Market data & OCR\n\n"
        "🔜 **Phase 2** — RAG & Sentiment\n\n"
        "🔜 **Phase 3** — Indian Tax & SIP\n\n"
        "🔜 **Phase 4** — LangGraph Orchestrator"
    )

# ── Route ─────────────────────────────────────────────────────────────────────
if page == "📈 Market Dashboard":
    market_dashboard.render()
elif page == "💸 Expense Tracker":
    expense_tracker.render()
