import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REFACTORED_DIR = Path(__file__).resolve().parent.parent

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

CM2W_API_BASE_URL = "https://app.cm2w.net/cm2w-api/v2/api-key-auth"
CM2W_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1NjI4NDQ4MzkxNSwibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.MHOogWqC84PZOBDvl-KlASj07Ly-CuyqBbcIj8KFmsc"

CONFIG_DIR = BASE_DIR / "Config"
UPLOADS_DIR = REFACTORED_DIR / "uploads"
EXCEL_LISTINGS_DIR = UPLOADS_DIR / "excel_listings"
REPORTS_DIR = BASE_DIR / "Reports"

DATA_CACHE_DIR = REFACTORED_DIR / "cache"
DATA_CACHE_DIR.mkdir(exist_ok=True)

REPORTS_OUTPUT_DIR = REFACTORED_DIR / "reports"
REPORTS_OUTPUT_DIR.mkdir(exist_ok=True)

PDF_OUTPUT_DIR = REFACTORED_DIR / "reports"
PDF_OUTPUT_DIR.mkdir(exist_ok=True)

CACHE_TTL_SECONDS = 3600
