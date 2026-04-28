"""
core/state.py
-------------
Defines the shared LangGraph State schema.

Even though LangGraph is only wired up in Phase 4, we define the State
shape NOW so that all tool functions are designed with it in mind.
This prevents a painful refactor later.

Why TypedDict?  LangGraph requires the State to be a TypedDict so it can
perform structured message passing between nodes.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class UserProfile(TypedDict, total=False):
    """Persisted user preferences and budget settings."""
    user_id: str
    monthly_budget: float          # INR
    risk_profile: str              # "conservative" | "moderate" | "aggressive"
    watchlist: List[str]           # e.g. ["RELIANCE.NS", "INFY.NS"]


class MarketContext(TypedDict, total=False):
    """Snapshot of the current market research context."""
    symbol: str
    current_price: float
    rsi: float
    ma_20: float
    ma_50: float
    volatility: float
    sentiment_score: float         # -1.0 (bearish) to +1.0 (bullish)
    last_fetched_at: str           # ISO timestamp


class ExpenseContext(TypedDict, total=False):
    """Context built up from a parsed receipt / UPI screenshot."""
    raw_ocr_text: str
    vendor: str
    amount: float
    category: str                  # e.g. "Food", "Transport", "Utilities"
    transaction_date: str
    confidence: float              # OCR extraction confidence 0–1


class AgentState(TypedDict, total=False):
    """
    Master state object passed between LangGraph nodes.

    Fields are Optional / total=False so individual nodes can populate
    only the parts they own — the orchestrator merges them.
    """
    # ── Conversation ──────────────────────────────────────────────────────────
    messages: List[Dict[str, str]]      # [{"role": "user", "content": "..."}]
    user_intent: str                     # Classified intent: "market" | "expense" | "rag" | "hybrid"

    # ── Sub-contexts (populated by expert nodes) ───────────────────────────────
    user_profile: UserProfile
    market_ctx: MarketContext
    expense_ctx: ExpenseContext
    rag_results: List[Dict[str, Any]]   # Retrieved knowledge chunks

    # ── Final response ────────────────────────────────────────────────────────
    final_response: str
    disclaimer: str                      # Always appended: "Not certified financial advice."
