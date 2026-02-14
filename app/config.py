"""
ChitChat configuration. Extend with INVITE_CODE, SECRET_KEY, DB path, etc.
Loads .env from project root if present.
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# Load .env before reading config (so env vars override .env)
_dotenv_path = BASE_DIR / ".env"
if _dotenv_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_dotenv_path)


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("CHITCHAT_SECRET_KEY", "dev-secret-change-in-production")
    # Koyeb/Heroku use DATABASE_URL; we also support CHITCHAT_DATABASE_URI and others
    _db_uri = (
        os.environ.get("CHITCHAT_DATABASE_URI")
        or os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("NEON_DATABASE_URL")
    )
    if not _db_uri or not (_db_uri := _db_uri.strip()):
        _db_uri = "sqlite:///" + str(BASE_DIR / "instance" / "chitchat.db").replace("\\", "/")
    elif _db_uri.startswith("postgres://"):
        _db_uri = _db_uri.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Server name/branding (shown in header)
    SERVER_NAME = os.environ.get("CHITCHAT_SERVER_NAME", "No Homers Club")
    # Simple Invite Code (pre-defined in config)
    INVITE_CODE = os.environ.get("CHITCHAT_INVITE_CODE", "chitchat-invite")
    # Remember logged-in users for 30 days (cookie persists across browser restarts)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    REMEMBER_COOKIE_NAME = "chitchat_remember"
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    # File/image uploads (instance/uploads/)
    UPLOAD_FOLDER = BASE_DIR / "instance" / "uploads"
    MAX_CONTENT_LENGTH = int(os.environ.get("CHITCHAT_MAX_UPLOAD_MB", "5")) * 1024 * 1024  # 5 MB default
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg", "pdf", "txt", "zip"}
    # Koyeb: use polling only when WebSocket fails (HTTP/2). Default True in production (Postgres).
    _polling_env = os.environ.get("CHITCHAT_SOCKET_POLLING_ONLY", "").strip().lower()
    _is_production = bool(_db_uri and "postgresql" in _db_uri)
    SOCKET_POLLING_ONLY = (
        _polling_env in ("1", "true", "yes")
        or (_is_production and _polling_env not in ("0", "false", "no"))
    )
    # Rate limit: max messages per user per minute (0 = disabled)
    MESSAGES_PER_MINUTE = int(os.environ.get("CHITCHAT_MESSAGES_PER_MINUTE", "60"))