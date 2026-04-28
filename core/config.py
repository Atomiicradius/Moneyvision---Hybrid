"""
core/config.py
--------------
Centralised configuration loader.
All API keys and environment variables are read here — never hardcoded elsewhere.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Reads from .env in the project root

# ── Market Data ──────────────────────────────────────────────────────────────
ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# ── LLM Provider ─────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY: str   = os.getenv("GROQ_API_KEY", "")     # Free-tier alternative

# ── Database ──────────────────────────────────────────────────────────────────
POSTGRES_URL: str = os.getenv(
    "POSTGRES_URL", "postgresql://postgres:password@localhost:5432/finintel"
)

# ── OCR ───────────────────────────────────────────────────────────────────────
GOOGLE_VISION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
FAISS_DIR  = os.path.join(BASE_DIR, "data", "vector_store")

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FAISS_DIR,  exist_ok=True)

# ── Market Constants (India-specific) ─────────────────────────────────────────
MARKET_OPEN_TIME  = "09:15"   # IST
MARKET_CLOSE_TIME = "15:30"   # IST
MARKET_TIMEZONE   = "Asia/Kolkata"
DEFAULT_CURRENCY  = "INR"
