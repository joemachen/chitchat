"""
Authentication: invite-code gating, registration, login, remember-me token.
"""
import time
from pathlib import Path

from flask import current_app
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User, db

REMEMBER_COOKIE_NAME = "chitchat_remember"
REMEMBER_TOKEN_FILENAME = "remember_token"


def _remember_serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt="chitchat-remember",
        signer_kwargs={"key_derivation": "hmac", "digest_method": "sha256"},
    )


def create_remember_token(user_id: int, username: str) -> str:
    """Create a signed token for remember-me cookie."""
    payload = {"user_id": user_id, "username": username, "t": int(time.time())}
    return _remember_serializer().dumps(payload)


def load_remember_token(token: str) -> tuple[int, str] | None:
    """Verify token and return (user_id, username) or None. Max age 30 days."""
    duration = current_app.config.get("REMEMBER_COOKIE_DURATION")
    max_age = int(duration.total_seconds()) if duration else 30 * 86400
    try:
        payload = _remember_serializer().loads(token, max_age=max_age)
        return (int(payload["user_id"]), str(payload["username"]))
    except (BadSignature, KeyError, TypeError, ValueError):
        return None


def _remember_token_path():
    return Path(current_app.instance_path) / REMEMBER_TOKEN_FILENAME


def save_remember_token_to_disk(token: str) -> None:
    """Persist remember token to disk (works when standalone window doesn't keep cookies)."""
    path = _remember_token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token, encoding="utf-8")


def load_remember_token_from_disk() -> str | None:
    """Read remember token from disk. Returns None if missing or unreadable."""
    path = _remember_token_path()
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def clear_remember_token_from_disk() -> None:
    """Remove remember token file (on logout)."""
    path = _remember_token_path()
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def validate_invite_code(code: str) -> bool:
    """Return True if code matches configured invite code."""
    return code == current_app.config.get("INVITE_CODE", "")


def register_user(username: str, password: str, invite_code: str) -> tuple[User | None, str]:
    """
    Register a new user if invite code is valid and username is available.
    Returns (user, error_message). user is None on failure.
    """
    if not validate_invite_code(invite_code):
        return None, "Invalid invite code."
    if not username or not username.strip():
        return None, "Username required."
    if not password or len(password) < 4:
        return None, "Password must be at least 4 characters."
    username = username.strip()
    if User.query.filter_by(username=username).first():
        return None, "Username already taken."
    user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return user, ""


def get_user_by_credentials(username: str, password: str) -> User | None:
    """Return user if username and password match."""
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None


def get_user_by_id(user_id: int) -> User | None:
    """Return user by primary key."""
    return User.query.get(user_id)


def reset_password(username: str, invite_code: str, new_password: str) -> tuple[bool, str]:
    """
    Set a new password for an existing user if invite code is valid.
    Returns (True, "") on success, (False, error_message) on failure.
    """
    if not validate_invite_code(invite_code):
        return False, "Invalid invite code."
    username = (username or "").strip()
    if not username:
        return False, "Username required."
    if not new_password or len(new_password) < 4:
        return False, "New password must be at least 4 characters."
    user = User.query.filter_by(username=username).first()
    if not user:
        return False, "No account with that username."
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return True, ""
