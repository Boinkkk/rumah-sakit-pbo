from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "medikacare.db"

DATABASE_URL = os.getenv(
    "MEDIKACARE_DATABASE_URL",
    f"sqlite+aiosqlite:///{DB_PATH.as_posix()}",
)
SECRET_KEY = os.getenv(
    "MEDIKACARE_SECRET_KEY",
    "medikacare-pbo-utm-2026-secret-key-change-in-prod",
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480
CLINIC_NAME = "Klinik Pratama Sehat"
APP_NAME = "MedikaCare"
