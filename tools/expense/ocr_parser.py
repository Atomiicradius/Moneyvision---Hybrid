"""
tools/expense/ocr_parser.py
----------------------------
Phase 1 — Expense Expert: OCR Text Extraction

Extracts raw text from UPI payment screenshots and receipts.
Uses Tesseract (free, local) with a fallback path for Google Vision (Phase 2+).

Why Tesseract first?
  - Zero API cost, runs offline
  - Sufficient for printed receipts and clean UPI message screenshots
  - Google Vision is reserved for blurry/handwritten receipts (Phase 2)
"""

from __future__ import annotations

import re
import os
from typing import Dict, Any, Optional
from pathlib import Path

from PIL import Image
import pytesseract

from core.config import UPLOAD_DIR
from core.logger import get_logger

logger = get_logger(__name__)

# ── Tesseract config ──────────────────────────────────────────────────────────
# On Windows, Tesseract is typically installed at this path.
# Users can override via the TESSERACT_CMD env var.
TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Tesseract config string:
#   --oem 3  → LSTM neural net engine (most accurate)
#   --psm 6  → Assume a single uniform block of text
TESS_CONFIG = "--oem 3 --psm 6"


def extract_text_from_image(image_path: str) -> Dict[str, Any]:
    """
    Run Tesseract OCR on a receipt or UPI screenshot.

    Args:
        image_path: Absolute path to the image file (.jpg, .png, .webp)

    Returns:
        Dict with keys:
          - raw_text (str):        Full OCR output
          - confidence (float):    Average character confidence 0.0–1.0
          - image_path (str):      Echo of input path
          - engine (str):          "tesseract"

    Raises:
        FileNotFoundError: If image_path does not exist
        RuntimeError:      If Tesseract is not installed / not found
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    logger.info(f"Running OCR on: {path.name}")

    try:
        img = Image.open(path).convert("RGB")

        # Get text
        raw_text = pytesseract.image_to_string(img, config=TESS_CONFIG)

        # Get per-character confidence scores
        data = pytesseract.image_to_data(
            img, config=TESS_CONFIG, output_type=pytesseract.Output.DICT
        )
        confidences = [
            int(c) for c in data["conf"] if str(c).lstrip("-").isdigit() and int(c) >= 0
        ]
        avg_confidence = round(sum(confidences) / len(confidences) / 100, 3) if confidences else 0.0

    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract is not installed or not found. "
            f"Expected at: {TESSERACT_CMD}\n"
            "Install from: https://github.com/UB-Mannheim/tesseract/wiki"
        )

    logger.debug(f"OCR confidence: {avg_confidence:.1%} | chars: {len(raw_text)}")

    return {
        "raw_text":   raw_text.strip(),
        "confidence": avg_confidence,
        "image_path": str(image_path),
        "engine":     "tesseract",
    }


def parse_upi_message(text: str) -> Dict[str, Any]:
    """
    Parse structured fields from a raw UPI payment SMS / notification text.

    Handles common UPI SMS formats from HDFC, SBI, ICICI, Paytm, GPay etc.

    Args:
        text: Raw OCR text or copy-pasted SMS content

    Returns:
        Dict with keys: amount, vendor, transaction_id, date, upi_id
        All values are None if not found.

    Example input:
        "Rs.1,250.00 debited from A/c XXXX1234 on 28-04-2026
         to VPA zomato@icicipay. UPI Ref: 612345678901"

    Financial Note:
        UPI transaction IDs (12-digit) are used for dispute resolution —
        we store them to build a reliable expense audit trail.
    """
    result: Dict[str, Any] = {
        "amount":         None,
        "vendor":         None,
        "transaction_id": None,
        "date":           None,
        "upi_id":         None,
    }

    # ── Amount ────────────────────────────────────────────────────────────────
    # Matches: Rs.1,250.00 / INR 250 / ₹ 1250.50
    amount_match = re.search(
        r"(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]{1,2})?)", text, re.IGNORECASE
    )
    if amount_match:
        result["amount"] = float(amount_match.group(1).replace(",", ""))

    # ── UPI ID / VPA ──────────────────────────────────────────────────────────
    upi_match = re.search(r"[\w.\-]+@[\w]+", text)
    if upi_match:
        result["upi_id"] = upi_match.group(0)
        # Use the part before '@' as a vendor hint
        result["vendor"] = upi_match.group(0).split("@")[0].replace(".", " ").title()

    # ── UPI Reference / Transaction ID ────────────────────────────────────────
    ref_match = re.search(r"(?:UPI Ref|Ref No|Txn ID)[:\s]*([0-9]{10,15})", text, re.IGNORECASE)
    if ref_match:
        result["transaction_id"] = ref_match.group(1)

    # ── Date ──────────────────────────────────────────────────────────────────
    date_match = re.search(
        r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{2}-[A-Za-z]{3}-\d{4})", text
    )
    if date_match:
        result["date"] = date_match.group(1)

    logger.debug(f"UPI parse result: {result}")
    return result


def save_uploaded_image(file_bytes: bytes, filename: str) -> str:
    """
    Save an uploaded image to the data/uploads directory.

    Args:
        file_bytes: Raw bytes from Streamlit's file_uploader
        filename:   Original filename

    Returns:
        Absolute path where the file was saved.
    """
    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(file_bytes)
    logger.info(f"Saved upload: {save_path}")
    return save_path
