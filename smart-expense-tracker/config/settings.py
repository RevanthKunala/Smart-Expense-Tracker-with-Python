"""
config/settings.py
Application configuration loaded from environment variables.
Uses python-dotenv to read a .env file in the project root.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one directory above this file)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Config:
    # ── Security ─────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # ── MySQL connection ──────────────────────────────────────────
    MYSQL_HOST     = os.environ.get("MYSQL_HOST",     "localhost")
    MYSQL_PORT     = int(os.environ.get("MYSQL_PORT", 3306))
    MYSQL_USER     = os.environ.get("MYSQL_USER",     "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB       = os.environ.get("MYSQL_DB",       "smart_expense_tracker")

    # ── CSRF (Flask-WTF) ─────────────────────────────────────────
    WTF_CSRF_ENABLED    = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # ── Sessions ──────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY      = True
    SESSION_COOKIE_SAMESITE      = "Lax"
    PERMANENT_SESSION_LIFETIME   = 1800  # 30 minutes


class DevelopmentConfig(Config):
    DEBUG                = True
    SESSION_COOKIE_SECURE = False   # HTTP is fine locally


class ProductionConfig(Config):
    DEBUG                = False
    SESSION_COOKIE_SECURE = True    # HTTPS required in production


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
}
