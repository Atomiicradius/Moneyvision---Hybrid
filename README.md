#  FinIntel Hybrid — AI-Powered Financial Intelligence Agent

FinIntel Hybrid is a modular, production-structured AI agent that merges two financial domains into one intelligent system:

1. **Market Research Intelligence** — Live NSE/BSE stock analysis with technical indicators
2. **Personal Finance Management** — OCR-based expense tracking from UPI screenshots & receipts

Built with Python 3.10+, LangChain, LangGraph (Phase 4), FastAPI, and Streamlit.

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Atomiicradius/Fintel-Hybrid.git
cd Fintel-Hybrid

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# 5. Run the app
streamlit run ui/app.py
```

App will open at → **http://localhost:8501**

---

## Project Structure

```
FinIntel-Hybrid/
├── core/                        # Shared utilities (used by all modules)
│   ├── config.py                # API keys & paths loaded from .env
│   ├── state.py                 # LangGraph AgentState schema
│   └── logger.py                # IST-timezone-aware logger
│
├── tools/                       # Expert modules (the heart of the system)
│   ├── market/
│   │   ├── stock_data.py        # yfinance: price fetch, OHLCV history
│   │   └── indicators.py        # RSI, Moving Averages, Volatility
│   ├── expense/
│   │   ├── ocr_parser.py        # Tesseract OCR + UPI SMS regex parser
│   │   └── categorizer.py       # Rule-based expense classification
│   └── rag/                     # Phase 2: Vector DB knowledge retrieval
│
├── agents/                      # Phase 4: LangGraph orchestrator
│   └── orchestrator.py
│
├── ui/
│   ├── app.py                   # Streamlit entry point + navigation
│   └── pages/
│       ├── market_dashboard.py  # Candlestick chart, RSI, MA, signals
│       └── expense_tracker.py   # Upload receipts, categorise, visualise
│
├── tests/
│   ├── test_market.py           # pytest: stock data + indicators
│   └── test_ocr.py              # pytest: UPI parser + categorizer
│
├── data/
│   ├── uploads/                 # Receipt images (gitignored)
│   └── vector_store/            # FAISS index files (gitignored)
│
├── .env.example                 # Template for environment variables
├── .gitignore
└── requirements.txt
```

---

## 🗺️ 8-Week Roadmap

| Phase | Weeks | Focus | Status |
|-------|-------|-------|--------|
| **Phase 1** | 1–2 | yfinance integration + OCR + Streamlit UI | ✅ **Done** |
| **Phase 2** | 3–4 | RAG (FAISS/pgvector) + News Sentiment | 🔜 |
| **Phase 3** | 5–6 | Indian Tax logic, SIP calculators, Splitwise | 🔜 |
| **Phase 4** | 7–8 | LangGraph Orchestrator (full agentic reasoning) | 🔜 |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Market Data | yfinance, Alpha Vantage |
| OCR | Tesseract, Google Vision (Phase 2) |
| AI Framework | LangChain, LangGraph |
| Vector DB | FAISS → pgvector (Phase 2) |
| UI | Streamlit (Phase 1–3) → React (Phase 4) |
| Charts | Plotly |
| Database | PostgreSQL + pgvector |
