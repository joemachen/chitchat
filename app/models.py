"""
SQLAlchemy models: User, Room, Message, IgnoreList.
"""
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, UniqueConstraint

db = SQLAlchemy()


def _isoformat_utc(dt):
    """Serialize naive UTC datetime for JS; append Z so Date() parses as UTC."""
    return (dt.isoformat() + "Z") if dt else None


class User(db.Model):
    """Registered user. No open sign-up; requires invite code to register."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    room_order_ids = db.Column(db.Text, nullable=True)  # JSON array of room ids, e.g. "[1,2,3]"
    is_super_admin = db.Column(db.Boolean, nullable=False, default=False)
    rank = db.Column(db.String(20), nullable=False, default="rookie")  # rookie | bro | fam | super_admin (lowest to highest)
    away_message = db.Column(db.Text, nullable=True)
    display_name = db.Column(db.String(80), nullable=True)  # /nick; shown in chat when set
    status_line = db.Column(db.String(120), nullable=True)  # /status
    bio = db.Column(db.String(200), nullable=True)  # Short bio shown in whois
    avatar_bg_color = db.Column(db.String(7), nullable=True)  # Hex color for letter avatar, e.g. #5865F2
    user_status = db.Column(db.String(20), nullable=False, default="online")  # online | away | dnd
    last_seen = db.Column(db.DateTime, nullable=True)  # Updated on disconnect for /whois
    message_retention_days = db.Column(db.Integer, nullable=True)  # None = keep forever; 7/30/90 = auto-delete after N days

    messages = db.relationship("Message", backref="user", lazy="dynamic", foreign_keys="Message.user_id")
    ignoring = db.relationship(
        "IgnoreList",
        foreign_keys="IgnoreList.user_id",
        backref="user",
        lazy="dynamic",
    )
    ignored_by = db.relationship(
        "IgnoreList",
        foreign_keys="IgnoreList.ignored_user_id",
        backref="ignored_user",
        lazy="dynamic",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "created_at": _isoformat_utc(self.created_at),
            "is_super_admin": getattr(self, "is_super_admin", False),
            "rank": getattr(self, "rank", None) or "rookie",
            "away_message": getattr(self, "away_message", None) or None,
            "display_name": getattr(self, "display_name", None) or None,
            "status_line": getattr(self, "status_line", None) or None,
            "user_status": getattr(self, "user_status", None) or "online",
            "last_seen": _isoformat_utc(getattr(self, "last_seen", None)),
            "avatar_bg_color": getattr(self, "avatar_bg_color", None) or None,
        }


class Room(db.Model):
    """Chat room. Full CRUD."""
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)
    topic = db.Column(db.Text, nullable=True)
    topic_set_by_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)
    topic_set_at = db.Column(db.DateTime, nullable=True)
    dm_with_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)  # If set, room is DM between created_by_id and dm_with_id
    is_protected = db.Column(db.Boolean, nullable=False, default=False)  # Surfer Girl can set; prevents delete by non-Surfer Girl

    created_by = db.relationship("User", backref="created_rooms", foreign_keys=[created_by_id])
    topic_set_by = db.relationship("User", foreign_keys=[topic_set_by_id])
    dm_with = db.relationship("User", foreign_keys=[dm_with_id])
    messages = db.relationship("Message", backref="room", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": _isoformat_utc(self.created_at),
            "created_by_id": self.created_by_id,
            "created_by_username": self.created_by.username if self.created_by else None,
            "topic": self.topic or "",
            "topic_set_by_id": self.topic_set_by_id,
            "topic_set_by_username": self.topic_set_by.username if self.topic_set_by else None,
            "topic_set_at": _isoformat_utc(self.topic_set_at),
            "dm_with_id": self.dm_with_id,
            "is_dm": self.dm_with_id is not None,
            "dm_with_username": self.dm_with.username if self.dm_with else None,
            "is_protected": getattr(self, "is_protected", False),
        }


class Message(db.Model):
    """Chat message in a room. Persisted for Discord-style history."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    message_type = db.Column(db.String(20), nullable=False, default="chat")  # "chat" or "emote"
    # Legacy: DB column "room" (string); model uses room_legacy so Room.messages backref can use "room"
    room_legacy = db.Column("room", db.String(120), nullable=True, default="")
    parent_id = db.Column(db.Integer, ForeignKey("messages.id"), nullable=True, index=True)
    edited_at = db.Column(db.DateTime, nullable=True)
    attachment_url = db.Column(db.String(512), nullable=True)  # /uploads/filename
    attachment_filename = db.Column(db.String(256), nullable=True)
    link_previews = db.Column(db.Text, nullable=True)  # JSON array of {url, title, description, image}

    parent = db.relationship("Message", remote_side=[id], backref=db.backref("replies", lazy="dynamic"))

    def to_dict(self) -> dict:
        user = self.user
        username = user.username if user else None
        display_name = getattr(user, "display_name", None) or None if user else None
        avatar_bg_color = getattr(user, "avatar_bg_color", None) or None if user else None
        out = {
            "id": self.id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "username": username,
            "display_name": display_name,
            "avatar_bg_color": avatar_bg_color,
            "content": self.content,
            "created_at": _isoformat_utc(self.created_at),
            "message_type": self.message_type or "chat",
            "parent_id": self.parent_id,
            "edited_at": _isoformat_utc(self.edited_at),
            "attachment_url": self.attachment_url,
            "attachment_filename": self.attachment_filename,
        }
        lp = getattr(self, "link_previews", None)
        if lp:
            try:
                out["link_previews"] = json.loads(lp) if isinstance(lp, str) else lp
            except (TypeError, ValueError):
                pass
        if self.parent_id and self.parent:
            p = self.parent
            p_user = p.user
            out["parent_content"] = p.content
            out["parent_username"] = p_user.username if p_user else None
            out["parent_display_name"] = (getattr(p_user, "display_name", None) or None) if p_user else None
        # Reactions: [{emoji, count, user_ids, usernames}]
        try:
            from collections import defaultdict
            by_emoji = defaultdict(list)
            reactions = getattr(self, "reactions", None)
            for r in (reactions.all() if hasattr(reactions, "all") else (reactions or [])):
                by_emoji[r.emoji].append(r.user_id)
            result = []
            all_ids = set()
            for ids in by_emoji.values():
                all_ids.update(ids)
            id_to_username = {}
            if all_ids:
                for u in User.query.filter(User.id.in_(all_ids)).all():
                    id_to_username[u.id] = u.username or f"User#{u.id}"
            for e, ids in sorted(by_emoji.items()):
                result.append({
                    "emoji": e,
                    "count": len(ids),
                    "user_ids": ids,
                    "usernames": [id_to_username.get(uid, f"User#{uid}") for uid in ids],
                })
            out["reactions"] = result
        except Exception:
            out["reactions"] = []
        return out


class IgnoreList(db.Model):
    """User A ignores User B. Frontend soft-hides B's messages for A."""
    __tablename__ = "ignore_list"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    ignored_user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "ignored_user_id", name="uq_ignore_pair"),)

    def to_dict(self) -> dict:
        return {"user_id": self.user_id, "ignored_user_id": self.ignored_user_id}


class RoomMute(db.Model):
    """User A mutes User B in Room R. A does not see B's messages in that room."""
    __tablename__ = "room_mutes"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    muted_user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    muted_by_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("room_id", "muted_user_id", "muted_by_id", name="uq_room_mute"),)


class UserRoomNotificationMute(db.Model):
    """User mutes notifications (unread dot) for a room."""
    __tablename__ = "user_room_notification_mute"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = db.Column(db.Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "room_id", name="uq_user_room_notification_mute"),)


class AcroScore(db.Model):
    """Persistent Acrophobia wins per room per user."""
    __tablename__ = "acro_scores"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    wins = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_acro_score"),)


class TriviaScore(db.Model):
    """Persistent trivia correct answers per room per user."""
    __tablename__ = "trivia_scores"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    correct = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_trivia_score"),)


class AppSetting(db.Model):
    """Key-value app config (e.g. default_room_id for login)."""
    __tablename__ = "app_settings"

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=True)


class RolePermission(db.Model):
    """Configurable permissions per role (rookie, bro, fam). Surfer Girl has all; others use this."""
    __tablename__ = "role_permissions"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, index=True)  # rookie | bro | fam
    permission = db.Column(db.String(40), nullable=False, index=True)
    allowed = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (UniqueConstraint("role", "permission", name="uq_role_permission"),)


class MessageReaction(db.Model):
    """User reaction (emoji) on a message. One user can add multiple emoji to same message."""
    __tablename__ = "message_reactions"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    emoji = db.Column(db.String(32), nullable=False)

    __table_args__ = (UniqueConstraint("message_id", "user_id", "emoji", name="uq_message_reaction"),)

    message = db.relationship("Message", backref=db.backref("reactions", lazy="dynamic", cascade="all, delete-orphan"))
    user = db.relationship("User", backref="message_reactions")


class UserRoomRead(db.Model):
    """Tracks last message id read per user per room for unread counts."""
    __tablename__ = "user_room_read"

    user_id = db.Column(db.Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    room_id = db.Column(db.Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    last_message_id = db.Column(db.Integer, nullable=False, default=0)


class MessageReport(db.Model):
    """User-reported message. For moderation and App Store compliance."""
    __tablename__ = "message_reports"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, ForeignKey("messages.id"), nullable=False, index=True)
    reported_by_user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False, index=True)
    reason = db.Column(db.Text, nullable=True)  # optional free text or category
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("message_id", "reported_by_user_id", name="uq_message_report"),)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "reported_by_user_id": self.reported_by_user_id,
            "reason": self.reason,
            "created_at": _isoformat_utc(self.created_at),
        }


class AuditLog(db.Model):
    """Audit trail of admin/moderation actions. Surfer Girl view only."""
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    target_type = db.Column(db.String(40), nullable=True)  # room, user, etc.
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)  # JSON or human-readable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="audit_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "created_at": _isoformat_utc(self.created_at),
        }
