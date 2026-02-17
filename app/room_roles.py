"""Room roles: owner, moderator, member. Room-level kick (ban)."""
from app.models import Room, RoomBan, RoomMember, User, db


def get_room_role(room_id: int, user_id: int) -> str | None:
    """Return role for user in room, or None if not in room_members (use created_by_id / global perms)."""
    m = RoomMember.query.filter_by(room_id=room_id, user_id=user_id).first()
    return m.role if m else None


def is_room_owner(room_id: int, user_id: int) -> bool:
    """True if user is room owner (explicit role or created_by_id for rooms without RoomMember)."""
    role = get_room_role(room_id, user_id)
    if role == "owner":
        return True
    room = Room.query.get(room_id)
    return room and room.created_by_id == user_id and room.dm_with_id is None


def is_room_moderator(room_id: int, user_id: int) -> bool:
    """True if user is room moderator or owner."""
    role = get_room_role(room_id, user_id)
    return role in ("owner", "moderator")


def is_banned_from_room(room_id: int, user_id: int) -> bool:
    """True if user is banned from sending messages in this room."""
    return RoomBan.query.filter_by(room_id=room_id, banned_user_id=user_id).first() is not None


def add_room_member(room_id: int, user_id: int, role: str = "member") -> RoomMember:
    """Add or update room member. role: owner | moderator | member."""
    m = RoomMember.query.filter_by(room_id=room_id, user_id=user_id).first()
    if m:
        m.role = role
    else:
        m = RoomMember(room_id=room_id, user_id=user_id, role=role)
        db.session.add(m)
    db.session.commit()
    return m


def set_room_moderator(room_id: int, user_id: int, is_moderator: bool) -> bool:
    """Set user as moderator (or demote to member). Caller must be owner. Returns True on success."""
    m = RoomMember.query.filter_by(room_id=room_id, user_id=user_id).first()
    if is_moderator:
        if m:
            m.role = "moderator"
        else:
            db.session.add(RoomMember(room_id=room_id, user_id=user_id, role="moderator"))
    else:
        if m and m.role == "moderator":
            m.role = "member"
        elif m and m.role == "owner":
            return False  # Cannot demote owner
    db.session.commit()
    return True


def ban_user_from_room(room_id: int, banned_user_id: int, banned_by_id: int) -> bool:
    """Ban user from room. Caller must be owner or moderator. Returns True on success."""
    if RoomBan.query.filter_by(room_id=room_id, banned_user_id=banned_user_id).first():
        return True  # Already banned
    db.session.add(RoomBan(room_id=room_id, banned_user_id=banned_user_id, banned_by_id=banned_by_id))
    db.session.commit()
    return True


def unban_user_from_room(room_id: int, banned_user_id: int) -> bool:
    """Remove room ban. Caller must be owner or moderator."""
    b = RoomBan.query.filter_by(room_id=room_id, banned_user_id=banned_user_id).first()
    if b:
        db.session.delete(b)
        db.session.commit()
        return True
    return False


def get_room_moderators(room_id: int) -> list[tuple[int, str]]:
    """Return list of (user_id, username) for moderators and owners."""
    members = RoomMember.query.filter(
        RoomMember.room_id == room_id,
        RoomMember.role.in_(["owner", "moderator"]),
    ).all()
    result = []
    for m in members:
        u = User.query.get(m.user_id)
        if u:
            result.append((u.id, u.username))
    return result
