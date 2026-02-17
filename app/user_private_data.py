"""Private user data: key/value store for preferences. Matrix-inspired."""
from datetime import datetime

from app.models import UserPrivateData, db


def get_private_data(user_id: int, key: str) -> str | None:
    """Get value for user's private data key. Returns None if not set."""
    row = UserPrivateData.query.filter_by(user_id=user_id, key=key).first()
    return row.value if row else None


def set_private_data(user_id: int, key: str, value: str | None) -> None:
    """Set value for user's private data key. value=None removes the key."""
    row = UserPrivateData.query.filter_by(user_id=user_id, key=key).first()
    if value is None:
        if row:
            db.session.delete(row)
    else:
        if row:
            row.value = value
            row.updated_at = datetime.utcnow()
        else:
            db.session.add(UserPrivateData(user_id=user_id, key=key, value=value))
    db.session.commit()


def get_all_private_data(user_id: int) -> dict[str, str]:
    """Return all key/value pairs for user."""
    rows = UserPrivateData.query.filter_by(user_id=user_id).all()
    return {r.key: r.value for r in rows if r.value is not None}
