"""
tests/test_ocr.py
------------------
Unit tests for the Expense Expert tools (categorizer + UPI parser).
OCR tests are separated since they require a real image and Tesseract install.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.expense.ocr_parser import parse_upi_message
from tools.expense.categorizer import categorize_expense, summarise_expenses


# ── UPI Parser ────────────────────────────────────────────────────────────────

SAMPLE_UPI_SMS = (
    "Rs.1,250.00 debited from A/c XXXX1234 on 28-04-2026 "
    "to VPA zomato@icicipay. UPI Ref: 612345678901"
)

def test_parse_upi_amount():
    result = parse_upi_message(SAMPLE_UPI_SMS)
    assert result["amount"] == 1250.0

def test_parse_upi_vendor():
    result = parse_upi_message(SAMPLE_UPI_SMS)
    assert result["vendor"] is not None
    assert "zomato" in result["vendor"].lower()

def test_parse_upi_transaction_id():
    result = parse_upi_message(SAMPLE_UPI_SMS)
    assert result["transaction_id"] == "612345678901"

def test_parse_upi_date():
    result = parse_upi_message(SAMPLE_UPI_SMS)
    assert "28-04-2026" in result["date"]

def test_parse_upi_no_match():
    result = parse_upi_message("Hello, how are you?")
    assert result["amount"] is None


# ── Categorizer ────────────────────────────────────────────────────────────────

def test_categorize_food():
    r = categorize_expense("Zomato", "zomato@icicipay", 350)
    assert r["category"] == "Food"
    assert r["confidence"] == 1.0
    assert r["method"] == "rule_based"

def test_categorize_transport():
    r = categorize_expense("Uber", "uber@ybl", 180)
    assert r["category"] == "Transport"

def test_categorize_fallback_small_amount():
    r = categorize_expense("UnknownShop", "", 50)
    assert r["category"] == "Food"   # Heuristic: small amount → food
    assert r["method"] == "heuristic_fallback"

def test_summarise_expenses():
    expenses = [
        {"category": "Food",      "amount": 350},
        {"category": "Food",      "amount": 120},
        {"category": "Transport", "amount": 80},
    ]
    totals = summarise_expenses(expenses)
    assert totals["Food"]      == 470.0
    assert totals["Transport"] == 80.0
