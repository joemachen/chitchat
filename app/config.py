"""
ChitChat configuration. Extend with INVITE_CODE, SECRET_KEY, DB path, etc.
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("CHITCHAT_SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "CHITCHAT_DATABASE_URI",
        f"sqlite:///{BASE_DIR / 'instance' / 'chitchat.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Simple Invite Code (pre-defined in config)
    INVITE_CODE = os.environ.get("CHITCHAT_INVITE_CODE", "chitchat-invite")
    # Remember logged-in users for 30 days (cookie persists across browser restarts)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    REMEMBER_COOKIE_NAME = "chitchat_remember"
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
