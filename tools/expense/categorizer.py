"""
tools/expense/categorizer.py
-----------------------------
Phase 1 — Expense Expert: LLM-based Expense Categorisation

Takes the parsed UPI/OCR data and classifies it into spending categories.

Phase 1: Rule-based fallback (no API key needed to get started).
Phase 2: Swap in an LLM call (OpenAI / Groq) for fuzzy classification.

Indian Expense Categories (aligned with common personal finance buckets):
  Food, Transport, Utilities, Shopping, Healthcare,
  Entertainment, Education, Rent, Insurance, Investments, Other
"""

from __future__ import annotations

import re
from typing import Dict, Any

from core.logger import get_logger

logger = get_logger(__name__)

# ── Category keyword map ───────────────────────────────────────────────────────
# Keys are category labels; values are lists of lowercase keywords/vendor hints.
# Phase 2: replace this with an LLM prompt for fuzzy + contextual matching.

CATEGORY_RULES: Dict[str, list[str]] = {
    "Food": [
        "zomato", "swiggy", "dominos", "mcdonald", "kfc", "subway",
        "restaurant", "cafe", "hotel", "food", "biryani", "pizza",
        "chai", "tea", "coffee", "dunzo", "blinkit", "zepto",
    ],
    "Transport": [
        "ola", "uber", "rapido", "metro", "irctc", "indigo", "airindia",
        "spicejet", "vistara", "yatra", "makemytrip", "redbus", "petrol",
        "diesel", "fuel", "fasttag", "parking",
    ],
    "Utilities": [
        "electricity", "bescom", "tata power", "adani", "reliance energy",
        "water", "gas", "bses", "msedcl", "tneb", "jio", "airtel",
        "vi ", "vodafone", "bsnl", "broadband", "internet",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa",
        "shopsy", "tata cliq", "store", "mart", "bazaar", "dmart",
        "bigbasket", "grofer",
    ],
    "Healthcare": [
        "pharmacy", "medplus", "apollo", "1mg", "netmeds", "doctor",
        "hospital", "clinic", "lab", "diagnostics", "healthkart",
    ],
    "Entertainment": [
        "netflix", "hotstar", "prime", "zee5", "sonyliv", "youtube",
        "spotify", "gaana", "jiosaavn", "bookmyshow", "pvr", "inox",
        "game", "steam",
    ],
    "Education": [
        "udemy", "coursera", "unacademy", "byju", "vedantu", "upgrad",
        "college", "university", "school", "fees", "books", "stationery",
    ],
    "Rent": ["rent", "pg ", "paying guest", "hostel", "accommodation"],
    "Insurance": ["lic", "hdfc life", "icici prudential", "star health", "bajaj allianz", "policy"],
    "Investments": ["zerodha", "groww", "upstox", "kuvera", "coin", "mutual fund", "sip", "nps"],
}

DISCLAIMER = "⚠️ This is for educational analysis, not certified financial advice."


def categorize_expense(vendor: str, upi_id: str = "", amount: float = 0.0) -> Dict[str, Any]:
    """
    Classify an expense into a spending category.

    Phase 1 implementation: Rule-based keyword matching.
    Phase 2 upgrade: Replace body with an LLM call for nuanced classification.

    Args:
        vendor:  Vendor name extracted from OCR / UPI ID
        upi_id:  Full UPI VPA (e.g. "zomato@icicipay") for extra signal
        amount:  Transaction amount in INR (used for heuristics in Phase 2)

    Returns:
        Dict with keys:
          - category (str):    Matched category label
          - confidence (float): 1.0 for rule match, 0.5 for fallback
          - method (str):      "rule_based" | "llm" (future)
          - disclaimer (str):  Mandatory disclaimer

    Example:
        >>> categorize_expense("Zomato", "zomato@icicipay", 350.0)
        {'category': 'Food', 'confidence': 1.0, 'method': 'rule_based', ...}
    """
    search_text = f"{vendor} {upi_id}".lower()

    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in search_text:
                logger.debug(f"Matched '{kw}' → {category}")
                return {
                    "category":   category,
                    "confidence": 1.0,
                    "method":     "rule_based",
                    "disclaimer": DISCLAIMER,
                }

    # ── Fallback: amount-based heuristics ────────────────────────────────────
    # Very rough heuristics when no keyword matches — Phase 2 replaces this.
    if 0 < amount <= 200:
        category = "Food"           # Small amounts → often food/tea
    elif 200 < amount <= 2000:
        category = "Shopping"
    else:
        category = "Other"

    logger.debug(f"No keyword match for '{vendor}' — fallback to '{category}'")
    return {
        "category":   category,
        "confidence": 0.5,          # Low confidence for heuristic match
        "method":     "heuristic_fallback",
        "disclaimer": DISCLAIMER,
    }


def summarise_expenses(expenses: list[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregate a list of categorised expenses into totals per category.

    Args:
        expenses: List of dicts, each with 'category' and 'amount' keys.

    Returns:
        Dict mapping category → total INR spent.

    Example:
        >>> summarise_expenses([
        ...     {"category": "Food", "amount": 350},
        ...     {"category": "Food", "amount": 120},
        ...     {"category": "Transport", "amount": 80},
        ... ])
        {'Food': 470.0, 'Transport': 80.0}
    """
    totals: Dict[str, float] = {}
    for exp in expenses:
        cat    = exp.get("category", "Other")
        amount = float(exp.get("amount", 0))
        totals[cat] = totals.get(cat, 0.0) + amount
    return totals
