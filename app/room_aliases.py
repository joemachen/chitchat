"""Room aliases: human-readable names (e.g. general, acrophobia) that resolve to room_id. Matrix-inspired."""
from app.models import Room, RoomAlias, db


def resolve_alias(alias: str) -> int | None:
    """Resolve alias to room_id. Alias is normalized (lowercase, strip #). Returns None if not found."""
    a = (alias or "").strip().lstrip("#").lower()
    if not a:
        return None
    row = RoomAlias.query.filter_by(alias=a).first()
    return row.room_id if row else None


def get_room_aliases(room_id: int) -> list[str]:
    """Return list of aliases for room."""
    rows = RoomAlias.query.filter_by(room_id=room_id).all()
    return [r.alias for r in rows]


def set_room_alias(room_id: int, alias: str) -> bool:
    """Add or update alias for room. Alias normalized. Returns True on success."""
    a = (alias or "").strip().lstrip("#").lower()
    if not a or len(a) > 80:
        return False
    existing = RoomAlias.query.filter_by(alias=a).first()
    if existing and existing.room_id != room_id:
        return False  # Alias taken by another room
    if existing:
        existing.room_id = room_id
    else:
        db.session.add(RoomAlias(room_id=room_id, alias=a))
    db.session.commit()
    return True


def remove_room_alias(room_id: int, alias: str) -> bool:
    """Remove alias from room."""
    a = (alias or "").strip().lstrip("#").lower()
    row = RoomAlias.query.filter_by(room_id=room_id, alias=a).first()
    if row:
        db.session.delete(row)
        db.session.commit()
        return True
    return False
