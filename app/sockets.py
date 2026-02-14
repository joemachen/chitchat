"""
Flask-SocketIO: join room (with history), send message, ignore list, user presence, stats.
Acrophobia game bot in room "Acrophobia". Super Admin: kick, channels, assign admins, settings.
"""
import eventlet
import json
import re
import time
from collections import Counter
from datetime import datetime

from flask import current_app, request, session
from flask_socketio import disconnect as socketio_disconnect, emit, join_room as socketio_join_room
from sqlalchemy import and_, extract, func, or_

from app.acrophobia import (
    SUBMIT_SECONDS,
    SUDDEN_DEATH_SUBMIT,
    SUDDEN_DEATH_VOTE,
    VOTE_SECONDS,
    advance_submit_phase,
    advance_vote_phase,
    get_phase_info as acrophobia_get_phase_info,
    get_submit_warning_message as acrophobia_get_submit_warning,
    get_vote_countdown_message as acrophobia_get_vote_countdown,
    handle_message as acrophobia_handle_message,
    is_acrobot_active,
    set_acrobot_active as acrophobia_set_acrobot_active,
)
from app.homer import get_random_simpsons_quote, is_homer_active, set_homer_active as homer_set_active
from app.link_preview import get_previews_for_message_content
from app.logging_config import get_logger
from app.models import AcroScore, AppSetting, AuditLog, IgnoreList, Message, MessageReaction, MessageReport, RolePermission, Room, RoomMute, User, UserRoomRead, _isoformat_utc, db

logger = get_logger()

_STOP_WORDS = frozenset(
    "a an the and or but in on at to for of with by is are was were be been being have has had do does did will would could should may might must shall can need i you he she it we they this that these those".split()
)

# Presence: user_id is "online" while they have an open socket
_online_user_ids = set()
_sid_to_user_id = {}

# Rate limit: user_id -> list of timestamps (last minute)
_rate_limit_timestamps = {}
_sid_to_connected_at = {}  # sid -> time.time() when connected
_sid_to_remote_addr = {}  # sid -> IP string
_user_id_to_room = {}  # user_id -> (room_id, room_name) for rich presence


def _get_users_with_online_status():
    """Return list of {id, username, online, is_super_admin, is_system_user} for all users, sorted by username.
    AcroBot's 'online' reflects the Settings toggle (is_acrobot_active), not socket presence.
    System user is a service account (posts system events), not a real connection; is_system_user=True so UI can show '(service)'."""
    users = User.query.order_by(User.username).all()
    online = set(_online_user_ids)
    result = []
    for u in users:
        rank = getattr(u, "rank", None) or "rookie"
        if u.username == "AcroBot":
            result.append({
                "id": u.id,
                "username": u.username,
                "display_name": None,
                "online": is_acrobot_active(),
                "is_super_admin": getattr(u, "is_super_admin", False),
                "rank": rank,
                "is_system_user": False,
                "user_status": "online",
                "current_room_name": None,
            })
        elif u.username == "System":
            result.append({
                "id": u.id,
                "username": u.username,
                "display_name": None,
                "online": False,
                "is_super_admin": getattr(u, "is_super_admin", False),
                "rank": rank,
                "is_system_user": True,
                "user_status": "online",
                "current_room_name": None,
            })
        elif u.username == "Homer":
            result.append({
                "id": u.id,
                "username": u.username,
                "display_name": None,
                "online": is_homer_active(),
                "is_super_admin": getattr(u, "is_super_admin", False),
                "rank": rank,
                "is_system_user": False,
                "user_status": "online",
                "current_room_name": None,
            })
        else:
            r = _user_id_to_room.get(u.id)
            result.append({
                "id": u.id,
                "username": u.username,
                "display_name": getattr(u, "display_name", None) or None,
                "online": u.id in online,
                "is_super_admin": getattr(u, "is_super_admin", False),
                "rank": rank,
                "is_system_user": False,
                "user_status": getattr(u, "user_status", None) or "online",
                "current_room_name": r[1] if r else None,
            })
    return result


def _get_room_mutes_for_user(user_id, room_id):
    """Return set of user_ids that user_id has muted in room_id."""
    records = RoomMute.query.filter_by(room_id=room_id, muted_by_id=user_id).all()
    return {r.muted_user_id for r in records}


def _rooms_sorted_for_user(user_id):
    """Return rooms in user's preferred order. Channels: all. DMs: only those user participates in, deduplicated per pair."""
    all_rooms = list(Room.query.all())
    channels = [r for r in all_rooms if r.dm_with_id is None]
    dm_rooms = [r for r in all_rooms if r.dm_with_id is not None
                and (r.created_by_id == user_id or r.dm_with_id == user_id)]
    # Deduplicate DMs: same user pair may have multiple room records (legacy); keep oldest per pair
    seen_pairs = set()
    deduped_dms = []
    for r in sorted(dm_rooms, key=lambda x: x.id):
        pair = (min(r.created_by_id, r.dm_with_id), max(r.created_by_id, r.dm_with_id))
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            deduped_dms.append(r)
    all_rooms = {r.id: r for r in channels + deduped_dms}
    user = User.query.get(user_id)
    order_ids = []
    if user and user.room_order_ids:
        try:
            order_ids = json.loads(user.room_order_ids)
        except (TypeError, ValueError):
            pass
    ordered = [all_rooms[rid] for rid in order_ids if rid in all_rooms]
    remaining = [r for rid, r in sorted(all_rooms.items(), key=lambda x: x[1].name) if r.id not in order_ids]
    return ordered + remaining


def _get_stats():
    """Compute stats from Message table: top typers, active hours, favorite words per user (top 10s)."""
    # Top 10 typers (message count per user)
    top_typers_q = (
        db.session.query(Message.user_id, func.count(Message.id).label("count"))
        .group_by(Message.user_id)
        .order_by(func.count(Message.id).desc())
        .limit(10)
        .all()
    )
    user_ids = [r[0] for r in top_typers_q]
    users_by_id = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()}
    top_typers = [
        {"user_id": uid, "username": users_by_id.get(uid).username if users_by_id.get(uid) else "?", "count": c}
        for uid, c in top_typers_q
    ]
    # Active hours by day (0-6) and hour (0-23): vertical bar chart with days overlapped
    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    active_hours_by_day = []
    try:
        dialect = db.session.get_bind().dialect.name
        if dialect == "postgresql":
            dow_expr = extract("dow", Message.created_at)  # 0=Sun
            hour_expr = extract("hour", Message.created_at)
        else:
            dow_expr = func.strftime("%w", Message.created_at)  # 0=Sun, returns string
            hour_expr = func.strftime("%H", Message.created_at)
        rows = (
            db.session.query(dow_expr.label("dow"), hour_expr.label("hour"), func.count(Message.id).label("count"))
            .group_by(dow_expr, hour_expr)
            .all()
        )
        # Build {dow: {hour: count}}
        by_day = {d: {h: 0 for h in range(24)} for d in range(7)}
        for dow, hour, count in rows:
            try:
                d = int(dow) if dow is not None else 0
                h = int(hour) if hour is not None else 0
                if 0 <= d <= 6 and 0 <= h <= 23:
                    by_day[d][h] = count
            except (TypeError, ValueError):
                pass
        for d in range(7):
            active_hours_by_day.append({
                "day": day_names[d],
                "day_num": d,
                "counts": [by_day[d][h] for h in range(24)],
            })
    except Exception:
        active_hours_by_day = [{"day": day_names[d], "day_num": d, "counts": [0] * 24} for d in range(7)]
    # Favorite words per user (top 5 users, top 10 words each; exclude stop words)
    all_msgs = Message.query.filter(Message.message_type == "chat").with_entities(Message.user_id, Message.content).all()
    word_re = re.compile(r"[a-z0-9']+", re.I)
    user_words = {}
    for uid, content in all_msgs:
        if not content:
            continue
        words = [w.lower() for w in word_re.findall(content) if len(w) > 1 and w.lower() not in _STOP_WORDS]
        user_words.setdefault(uid, []).extend(words)
    top_users_by_msg = [r[0] for r in top_typers_q[:5]]
    favorite_words = []
    for uid in top_users_by_msg:
        counts = Counter(user_words.get(uid, [])).most_common(10)
        u = users_by_id.get(uid)
        favorite_words.append(
            {"user_id": uid, "username": u.username if u else "?", "words": [{"word": w, "count": c} for w, c in counts]}
        )
    # Acrophobia leaderboard (Acrophobia room only)
    acro_room = Room.query.filter_by(name="Acrophobia").first()
    acro_leaderboard = []
    if acro_room:
        acro_rows = AcroScore.query.filter_by(room_id=acro_room.id).order_by(AcroScore.wins.desc()).limit(10).all()
        acro_user_ids = [r.user_id for r in acro_rows]
        acro_users = {u.id: u.username for u in User.query.filter(User.id.in_(acro_user_ids)).all()}
        acro_leaderboard = [
            {"user_id": r.user_id, "username": acro_users.get(r.user_id) or "?", "wins": r.wins}
            for r in acro_rows
        ]
    return {
        "top_typers": top_typers,
        "active_hours_by_day": active_hours_by_day,
        "favorite_words": favorite_words,
        "acro_leaderboard": acro_leaderboard,
    }


def _netsplit_reconnect(app, room_id: int, names: str, sys_user_id: int) -> None:
    """Post netsplit reconnection message (called from eventlet.spawn_after)."""
    with app.app_context():
        sys_user = User.query.get(sys_user_id)
        if sys_user:
            msg = Message(
                room_id=room_id,
                user_id=sys_user_id,
                content=f"*** End of netsplit. {names} have reconnected.",
                message_type="chat",
            )
            db.session.add(msg)
            db.session.commit()
            socket_io = getattr(app, "socketio", None)
            if socket_io:
                _broadcast_new_message_impl(socket_io, room_id, msg.to_dict())


def broadcast_system_event(app, content: str) -> None:
    """Post a system event to System Events room. Call from anywhere; pass app for context."""
    with app.app_context():
        sys_room = Room.query.filter_by(name="System Events").first()
        sys_user = User.query.filter_by(username="System").first()
        if sys_room and sys_user:
            msg = Message(
                room_id=sys_room.id,
                user_id=sys_user.id,
                content=content,
                message_type="chat",
            )
            db.session.add(msg)
            db.session.commit()
            socket_io = getattr(app, "socketio", None)
            if socket_io:
                _broadcast_new_message_impl(socket_io, sys_room.id, msg.to_dict())


def _broadcast_new_message_impl(socket_io, room_id, msg_dict):
    """Emit new_message to room and unread_incremented to users not viewing it. Module-level for use in callbacks."""
    if socket_io:
        socket_io.emit("new_message", msg_dict, room=f"room_{room_id}")
        current_viewing = {uid: rid for uid, (rid, _) in _user_id_to_room.items()}
        for uid in set(_sid_to_user_id.values()):
            if current_viewing.get(uid) == room_id:
                continue
            rooms = _rooms_sorted_for_user(uid)
            if any(ro.id == room_id for ro in rooms):
                socket_io.emit("unread_incremented", {"room_id": room_id}, room=f"user_{uid}")


def _acrophobia_emit_bot_messages(app, room_id, replies):
    """Create Message records for AcroBot and emit to room. Run inside app.app_context()."""
    acrobot = User.query.filter_by(username="AcroBot").first()
    if not acrobot:
        return
    socket_io = getattr(app, "socketio", None)
    for text in replies:
        if not text:
            continue
        msg = Message(
            room_id=room_id,
            user_id=acrobot.id,
            content=text,
            message_type="chat",
        )
        db.session.add(msg)
        db.session.commit()
        _broadcast_new_message_impl(socket_io, room_id, msg.to_dict())


def _acrophobia_submit_warning_callback(app, room_id, seconds_left):
    """Called at 30s and 15s remaining in submit phase."""
    with app.app_context():
        from app.acrophobia import get_phase_info
        info = get_phase_info(room_id)
        if info.get("phase") == "submitting":
            msg = acrophobia_get_submit_warning(seconds_left)
            _acrophobia_emit_bot_messages(app, room_id, [msg])


def _acrophobia_vote_countdown_callback(app, room_id, seconds_left: int):
    """Called at 10, 9, 8, … 1 seconds remaining in vote phase."""
    with app.app_context():
        from app.acrophobia import get_phase_info
        info = get_phase_info(room_id)
        if info.get("phase") == "voting":
            msg = acrophobia_get_vote_countdown(seconds_left)
            _acrophobia_emit_bot_messages(app, room_id, [msg])


def _acrophobia_submit_timer_callback(app, room_id, sudden_death: bool = False):
    """Called when submit phase ends. Advance to voting and send bot messages; then schedule vote timer if we have submissions."""
    with app.app_context():
        replies, is_sudden = advance_submit_phase(room_id)
        _acrophobia_emit_bot_messages(app, room_id, replies)
        info = acrophobia_get_phase_info(room_id)
        socket_io = getattr(app, "socketio", None)
        if socket_io:
            socket_io.emit("acrophobia_phase", info, room=f"room_{room_id}")
        if info.get("phase") != "voting":
            return  # No submissions; phase went to idle
        vote_sec = SUDDEN_DEATH_VOTE if is_sudden else VOTE_SECONDS
        for s in range(min(15, vote_sec), 0, -1):
            eventlet.spawn_after(vote_sec - s, _acrophobia_vote_countdown_callback, app, room_id, s)
        eventlet.spawn_after(vote_sec, _acrophobia_vote_timer_callback, app, room_id)


def _acrophobia_vote_timer_callback(app, room_id):
    """Called when vote phase ends. Reveal winner and send bot messages; start next round or sudden death."""
    with app.app_context():
        replies, start_next, is_sudden_death, winner_info = advance_vote_phase(room_id)
        _acrophobia_emit_bot_messages(app, room_id, replies)
        socket_io = getattr(app, "socketio", None)
        if socket_io:
            info = acrophobia_get_phase_info(room_id)
            socket_io.emit("acrophobia_phase", info, room=f"room_{room_id}")
            if replies and "Winner:" in (replies[0] or ""):
                socket_io.emit("acrophobia_winner", {}, room=f"room_{room_id}")
            if winner_info:
                broadcast_system_event(app, f"**{winner_info['username']}** just won Acrophobia!")
                row = AcroScore.query.filter_by(room_id=room_id, user_id=winner_info["user_id"]).first()
                if row and row.wins >= 5 and row.wins % 5 == 0:
                    broadcast_system_event(app, f"🔥 **{winner_info['username']}** hit a {row.wins}-win streak in Acrophobia!")
        if start_next:
            if is_sudden_death:
                _schedule_sudden_death_submit_timer(room_id)
                if socket_io:
                    socket_io.emit("acrophobia_phase", acrophobia_get_phase_info(room_id), room=f"room_{room_id}")
            else:
                from app.acrophobia import _game, _start_round
                g = _game(room_id)
                rounds_left = g.get("rounds_remaining", 0)
                if rounds_left > 0:
                    next_replies = _start_round(room_id, rounds=rounds_left)
                    if next_replies:
                        _acrophobia_emit_bot_messages(app, room_id, next_replies)
                        _schedule_acrophobia_submit_timer(room_id)
                        if socket_io:
                            socket_io.emit("acrophobia_phase", acrophobia_get_phase_info(room_id), room=f"room_{room_id}")


def _schedule_acrophobia_submit_timer(room_id):
    """Schedule 30s/15s warnings and advance from submit phase to voting after SUBMIT_SECONDS."""
    app = current_app._get_current_object()
    eventlet.spawn_after(30, _acrophobia_submit_warning_callback, app, room_id, 30)
    eventlet.spawn_after(45, _acrophobia_submit_warning_callback, app, room_id, 15)
    eventlet.spawn_after(SUBMIT_SECONDS, _acrophobia_submit_timer_callback, app, room_id, False)


def _schedule_sudden_death_submit_timer(room_id):
    """Schedule sudden death submit phase (30s, no mid-phase warnings)."""
    app = current_app._get_current_object()
    eventlet.spawn_after(SUDDEN_DEATH_SUBMIT, _acrophobia_submit_timer_callback, app, room_id, True)


def _user_by_username(username: str):
    """Return User by username or None. Case-insensitive."""
    if not username or not str(username).strip():
        return None
    return User.query.filter(func.lower(User.username) == str(username).strip().lower()).first()


def _get_or_create_dm_room(user_id: int, other_user_id: int):
    """Return the DM room between user_id and other_user_id, creating it if needed. Used server-side (e.g. AcroBot DM)."""
    room = Room.query.filter(
        or_(
            and_(Room.created_by_id == user_id, Room.dm_with_id == other_user_id),
            and_(Room.created_by_id == other_user_id, Room.dm_with_id == user_id),
        ),
    ).first()
    if not room:
        room = Room(name="DM", created_by_id=user_id, dm_with_id=other_user_id)
        db.session.add(room)
        db.session.commit()
    return room


PRESENCE_BROADCAST_INTERVAL = 20  # seconds


def _periodic_presence_broadcast(socketio):
    """Broadcast user list periodically to correct any stale presence state on clients."""
    try:
        app = getattr(socketio, "app", None)
        if app and (_online_user_ids or _sid_to_user_id):
            with app.app_context():
                socketio.emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
    except Exception as e:
        logger.warning("Periodic presence broadcast failed: %s", e)
    eventlet.spawn_after(PRESENCE_BROADCAST_INTERVAL, _periodic_presence_broadcast, socketio)


def register_socket_handlers(socketio):
    """Register SocketIO event handlers."""
    eventlet.spawn_after(PRESENCE_BROADCAST_INTERVAL, _periodic_presence_broadcast, socketio)

    def _post_system_event(content: str):
        """Post a system message to the System Events room."""
        app = current_app._get_current_object()
        broadcast_system_event(app, content)

    @socketio.on("connect")
    def on_connect(auth=None):
        if not session.get("user_id"):
            return False
        user_id = session.get("user_id")
        user = User.query.get(user_id)
        username = user.username if user else "Unknown"
        was_offline = user_id not in _online_user_ids
        _sid_to_user_id[request.sid] = user_id
        _sid_to_connected_at[request.sid] = time.time()
        _sid_to_remote_addr[request.sid] = getattr(request, "remote_addr", None) or (request.environ.get("REMOTE_ADDR") if request.environ else None)
        _online_user_ids.add(user_id)
        socketio_join_room(f"user_{user_id}")  # For unread_incremented and other user-specific events
        if was_offline:
            _post_system_event(f"{username} came online")
        logger.info("Socket connected: user_id=%s", user_id)
        emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)

    @socketio.on("disconnect")
    def on_disconnect():
        user_id = _sid_to_user_id.get(request.sid)
        username = "Unknown"
        if user_id:
            user = User.query.get(user_id)
            username = user.username if user else "Unknown"
            if user and hasattr(user, "last_seen"):
                user.last_seen = datetime.utcnow()
                db.session.commit()
        _sid_to_user_id.pop(request.sid, None)
        _sid_to_connected_at.pop(request.sid, None)
        _sid_to_remote_addr.pop(request.sid, None)
        if user_id:
            _user_id_to_room.pop(user_id, None)
            # Only remove from online and post "went offline" when this is the last socket for this user
            other_sockets = [sid for sid, uid in _sid_to_user_id.items() if uid == user_id]
            if not other_sockets:
                _online_user_ids.discard(user_id)
                _post_system_event(f"{username} went offline")
                logger.info("Socket disconnected: user_id=%s (last socket)", user_id)
            emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)

    def _is_super_admin(user_id):
        """Return True if user is Surfer Girl (top level, all permissions)."""
        u = User.query.get(user_id)
        return u and getattr(u, "is_super_admin", False)

    def _has_permission(user_id, permission):
        """Return True if user has permission. Surfer Girl has all; else check RolePermission for user's rank."""
        if _is_super_admin(user_id):
            return True
        u = User.query.get(user_id)
        if not u:
            return False
        rank = (getattr(u, "rank", None) or "rookie").lower()
        if rank == "super_admin":
            return True
        rp = RolePermission.query.filter_by(role=rank, permission=permission).first()
        return rp and rp.allowed

    def _check_rate_limit(user_id):
        """Return (ok, msg). If not ok, user exceeded messages per minute."""
        limit = getattr(current_app.config, "MESSAGES_PER_MINUTE", 60) or 0
        if limit <= 0:
            return True, None
        now = time.time()
        cutoff = now - 60
        if user_id not in _rate_limit_timestamps:
            _rate_limit_timestamps[user_id] = []
        timestamps = _rate_limit_timestamps[user_id]
        timestamps[:] = [t for t in timestamps if t > cutoff]
        if len(timestamps) >= limit:
            return False, f"Rate limit: max {limit} messages per minute. Please slow down."
        timestamps.append(now)
        return True, None

    def _audit_log(user_id, action, target_type=None, target_id=None, details=None):
        """Record an audit log entry."""
        try:
            entry = AuditLog(
                user_id=user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=json.dumps(details) if isinstance(details, (dict, list)) else details,
            )
            db.session.add(entry)
            db.session.commit()
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

    def _get_role_permissions_dict():
        """Return {role: {permission: allowed}} for rookie, bro, fam."""
        result = {"rookie": {}, "bro": {}, "fam": {}}
        for rp in RolePermission.query.all():
            if rp.role in result:
                result[rp.role][rp.permission] = rp.allowed
        perms = ("create_room", "update_room", "delete_room", "kick_user", "set_user_rank", "acrobot_control", "homer_control", "reset_stats", "export_all")
        for role in result:
            for p in perms:
                if p not in result[role]:
                    result[role][p] = False
        return result

    def _get_default_room_id():
        """Return default room_id for login. Surfer Girl sets via Settings."""
        row = AppSetting.query.filter_by(key="default_room_id").first()
        if row and row.value:
            try:
                rid = int(row.value)
                if Room.query.get(rid) and not Room.query.get(rid).dm_with_id:
                    return rid
            except (TypeError, ValueError):
                pass
        general = Room.query.filter_by(name="general").first()
        if general:
            return general.id
        first = Room.query.filter(Room.dm_with_id.is_(None)).order_by(Room.id).first()
        return first.id if first else None

    def _room_id_from_data(data):
        rid = (data or {}).get("room_id")
        if rid is None:
            return _get_default_room_id()
        try:
            return int(rid)
        except (TypeError, ValueError):
            return None

    def _get_unread_counts(user_id):
        """Return {room_id: unread_count} for all rooms user has access to."""
        rooms = _rooms_sorted_for_user(user_id)
        result = {}
        for r in rooms:
            if r.name.strip().lower() == "stats":
                continue
            row = UserRoomRead.query.filter_by(user_id=user_id, room_id=r.id).first()
            last_id = row.last_message_id if row else 0
            count = Message.query.filter(Message.room_id == r.id, Message.id > last_id).count()
            if count > 0:
                result[r.id] = count
        return result

    def _broadcast_new_message(room_id, msg_dict):
        """Emit new_message to room and unread_incremented to users not viewing it."""
        _broadcast_new_message_impl(socketio, room_id, msg_dict)

    @socketio.on("get_rooms")
    def on_get_rooms(data=None):
        """Return list of all rooms in user's order."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        rooms = _rooms_sorted_for_user(user_id)
        unread_counts = _get_unread_counts(user_id)
        emit("rooms_list", {"rooms": [r.to_dict() for r in rooms], "unread_counts": unread_counts})

    @socketio.on("join_room")
    def on_join_room(data):
        """Join a room; server sends full message history and user's ignore list."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        room_id = _room_id_from_data(data)
        if not room_id:
            emit("error", {"message": "Invalid room"})
            return
        room_obj = Room.query.get(room_id)
        if not room_obj:
            emit("error", {"message": "Room not found"})
            return
        socket_room = f"room_{room_id}"
        socketio_join_room(socket_room)
        if room_obj.name.strip().lower() not in ("stats",):
            _user_id_to_room[user_id] = (room_id, room_obj.name)
            emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
        else:
            _user_id_to_room.pop(user_id, None)

        users_with_status = _get_users_with_online_status()
        rooms = _rooms_sorted_for_user(user_id)
        rooms_dict = [r.to_dict() for r in rooms]

        if room_obj.name.strip().lower() == "stats":
            unread_counts = _get_unread_counts(user_id)
            emit("room_joined", {
                "room": room_obj.to_dict(),
                "history": [],
                "stats": _get_stats(),
                "room_muted_in_room": [],
                "users": users_with_status,
                "rooms": rooms_dict,
                "has_more": False,
                "unread_counts": unread_counts,
            })
            logger.info("User %s joined stats room", user_id)
        else:
            # Paginate: last 50 messages, server-side room-mute filter
            room_mute_set = _get_room_mutes_for_user(user_id, room_id)
            q = Message.query.filter_by(room_id=room_id)
            if room_mute_set:
                q = q.filter(~Message.user_id.in_(room_mute_set))
            messages = q.order_by(Message.id.desc()).limit(51).all()
            has_more = len(messages) > 50
            messages = messages[:50]
            messages.reverse()
            history = [m.to_dict() for m in messages]
            room_muted_in_room = list(_get_room_mutes_for_user(user_id, room_id))
            last_msg_id = messages[-1].id if messages else 0
            urr = UserRoomRead.query.filter_by(user_id=user_id, room_id=room_id).first()
            if urr:
                urr.last_message_id = last_msg_id
            else:
                db.session.add(UserRoomRead(user_id=user_id, room_id=room_id, last_message_id=last_msg_id))
            db.session.commit()
            unread_counts = _get_unread_counts(user_id)
            payload = {
                "room": room_obj.to_dict(),
                "history": history,
                "room_muted_in_room": room_muted_in_room,
                "users": users_with_status,
                "rooms": rooms_dict,
                "has_more": has_more,
                "unread_counts": unread_counts,
            }
            if room_obj.name.strip() == "Acrophobia":
                payload["acrophobia"] = acrophobia_get_phase_info(room_id)
            emit("room_joined", payload)
            logger.info("User %s joined room %s, history len=%s", user_id, room_id, len(history))

    @socketio.on("user_typing")
    def on_user_typing(data):
        """Broadcast to room that this user is typing (client sends room_id)."""
        user_id = session.get("user_id")
        if not user_id:
            return
        room_id = _room_id_from_data(data)
        if not room_id:
            return
        user = User.query.get(user_id)
        if not user:
            return
        socket_room = f"room_{room_id}"
        socketio.emit(
            "user_typing",
            {"user_id": user_id, "username": user.username, "room_id": room_id},
            room=socket_room,
        )

    @socketio.on("load_more_messages")
    def on_load_more_messages(data):
        """Return older messages (paginated, server-side room-mute filter). Emit older_messages."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        room_id = (data or {}).get("room_id")
        before_id = (data or {}).get("before_id")
        if not room_id or before_id is None:
            emit("error", {"message": "room_id and before_id required"})
            return
        try:
            room_id = int(room_id)
            before_id = int(before_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid room_id or before_id"})
            return
        room_mute_set = _get_room_mutes_for_user(user_id, room_id)
        q = Message.query.filter_by(room_id=room_id).filter(Message.id < before_id)
        if room_mute_set:
            q = q.filter(~Message.user_id.in_(room_mute_set))
        messages = q.order_by(Message.id.desc()).limit(51).all()
        has_more = len(messages) > 50
        messages = messages[:50]
        messages.reverse()
        history = [m.to_dict() for m in messages]
        emit("older_messages", {"messages": history, "has_more": has_more})

    @socketio.on("send_message")
    def on_send_message(data):
        """Persist message and broadcast to room. Supports /ping username and /em (or /me) text."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        ok, err = _check_rate_limit(user_id)
        if not ok:
            emit("error", {"message": err})
            return
        room_id = _room_id_from_data(data)
        if not room_id:
            emit("error", {"message": "Invalid room"})
            return
        raw = (data or {}).get("content") or ""
        content = raw.strip()
        has_attachment = bool((data or {}).get("attachment_url"))
        if not content and not has_attachment:
            return
        room_obj = Room.query.get(room_id)
        if not room_obj:
            emit("error", {"message": "Room not found"})
            return
        user = User.query.get(user_id)
        if not user:
            emit("error", {"message": "User not found"})
            return

        # !Simpsons — Homer says a random Simpsons quote (when Homer is active)
        low_content = content.strip().lower()
        if low_content in ("!simpsons", "! simpsons"):
            if is_homer_active():
                homer_user = User.query.filter_by(username="Homer").first()
                if homer_user:
                    quote = get_random_simpsons_quote()
                    msg = Message(
                        room_id=room_id,
                        user_id=homer_user.id,
                        content=quote,
                        message_type="chat",
                    )
                    db.session.add(msg)
                    db.session.commit()
                    _broadcast_new_message(room_id, msg.to_dict())
            return

        # /netsplit — Easter egg: fake netsplit message
        if content.strip().lower() == "/netsplit":
            import random
            sys_user = User.query.filter_by(username="System").first()
            if sys_user:
                victims = list(
                    User.query.filter(
                        User.id != user_id,
                        User.username.notin_(["AcroBot", "System", "Homer"]),
                    ).limit(5).all()
                )
                if victims:
                    chosen = random.sample(victims, min(2, len(victims)))
                    names = ", ".join(u.username for u in chosen)
                    msg1 = Message(
                        room_id=room_id,
                        user_id=sys_user.id,
                        content=f"*** Netsplit! {names} have disconnected from the server.",
                        message_type="chat",
                    )
                    db.session.add(msg1)
                    db.session.commit()
                    _broadcast_new_message(room_id, msg1.to_dict())
                    app = current_app._get_current_object()
                    eventlet.spawn_after(3000, _netsplit_reconnect, app, room_id, names, sys_user.id)
                else:
                    msg1 = Message(
                        room_id=room_id,
                        user_id=sys_user.id,
                        content="*** Netsplit! Server A and Server B have lost connection.",
                        message_type="chat",
                    )
                    db.session.add(msg1)
                    db.session.commit()
                    _broadcast_new_message(room_id, msg1.to_dict())
                    app = current_app._get_current_object()
                    eventlet.spawn_after(3000, _netsplit_reconnect, app, room_id, "Server A and Server B", sys_user.id)
            return

        # DM with AcroBot: during Acrophobia submit phase, treat message as submission (so DMs count)
        if room_obj.dm_with_id is not None:
            other_id = room_obj.dm_with_id if room_obj.created_by_id == user_id else room_obj.created_by_id
            acrobot = User.query.filter_by(username="AcroBot").first()
            if acrobot and other_id == acrobot.id:
                acrophobia_room = Room.query.filter_by(name="Acrophobia").first()
                if acrophobia_room:
                    result = acrophobia_handle_message(acrophobia_room.id, user_id, user.username, content, from_dm=True)
                    consumed = result[0]
                    bot_replies = result[1]
                    dm_replies = result[2] if len(result) > 2 else []
                    if consumed:
                        for text in bot_replies:
                            if text:
                                msg = Message(
                                    room_id=acrophobia_room.id,
                                    user_id=acrobot.id,
                                    content=text,
                                    message_type="chat",
                                )
                                db.session.add(msg)
                                db.session.commit()
                                _broadcast_new_message(acrophobia_room.id, msg.to_dict())
                        for target_user_id, dm_text in dm_replies:
                            if dm_text:
                                dm_room = _get_or_create_dm_room(target_user_id, acrobot.id)
                                dm_msg = Message(
                                    room_id=dm_room.id,
                                    user_id=acrobot.id,
                                    content=dm_text,
                                    message_type="chat",
                                )
                                db.session.add(dm_msg)
                                db.session.commit()
                                _broadcast_new_message(dm_room.id, dm_msg.to_dict())
                        # Fall through so the user's message is also saved to the DM (shows their phrase + AcroBot reply)
                    # If not consumed (e.g. not in submit phase), fall through and save message to DM as normal

        # /m, /msg, /message <username> <text> — send a DM to that user (switch to DM, post message there)
        low_content = content.strip().lower()
        for prefix in ("/m ", "/msg ", "/message "):
            if low_content.startswith(prefix):
                rest = content[len(prefix):].strip()
                if not rest:
                    emit("error", {"message": f"Usage: {prefix.strip()} <username> <message>"})
                    return
                parts = rest.split(None, 1)
                to_username = (parts[0] or "").strip()
                msg_text = (parts[1] or "").strip() if len(parts) > 1 else ""
                if not to_username:
                    emit("error", {"message": f"Usage: {prefix.strip()} <username> <message>"})
                    return
                if to_username.lower() == "acrobot":
                    break  # Let AcroBot handlers below deal with /msg acrobot
                target = _user_by_username(to_username)
                if not target:
                    emit("error", {"message": f"User '{to_username}' not found"})
                    return
                if target.id == user_id:
                    emit("error", {"message": "Cannot message yourself"})
                    return
                existing = Room.query.filter(
                    or_(
                        and_(Room.created_by_id == user_id, Room.dm_with_id == target.id),
                        and_(Room.created_by_id == target.id, Room.dm_with_id == user_id),
                    ),
                ).first()
                if not existing:
                    dm_room = _get_or_create_dm_room(user_id, target.id)
                    rooms = Room.query.order_by(Room.name).all()
                    emit("rooms_updated", {"rooms": [r.to_dict() for r in rooms]}, broadcast=True)
                else:
                    dm_room = existing
                dm_msg = Message(
                    room_id=dm_room.id,
                    user_id=user_id,
                    content=msg_text or "(no message)",
                    message_type="chat",
                )
                db.session.add(dm_msg)
                db.session.commit()
                _broadcast_new_message(dm_room.id, dm_msg.to_dict())
                emit("dm_room", {"room": dm_room.to_dict()})
                return

        # /help — List all available slash commands (post as one message in channel)
        if content.strip().lower() == "/help":
            help_lines = [
                "**No Homers Club commands**",
                "• /help — show this list",
                "• /away [message] — set away; /dnd — Do Not Disturb; /online — back online",
                "• /nick <name> — set display name in chat; /nick to clear",
                "• /status <text> — set status (shown in /whois); /status to clear",
                "• /whois <username> — user info, last seen, shared rooms",
                "• /topic <text> — set channel topic",
                "• /ping <username> — notify that user",
                "• /m, /msg, /message <username> <text> — send a direct message to that user",
                "• @<nickname> <message> — page/mention that user (e.g. @Joe hey!)",
                "• /em <text> or /me <text> — third-person emote",
                "• !Simpsons — type in any room to trigger Homer; he replies with a random Simpsons quote (when Homer is online)",
                "• Right-click message → Reply, Add reaction, Edit, Delete, Hide, Mute, Report, Mark unread, View profile, Whois",
                "• Right-click user → View profile, Message, Kick (if permitted)",
                "• Ctrl+K — room switcher; Esc — close modals",
                "",
                "**In Acrophobia channel**",
                "• /help or /msg acrobot help — AcroBot help & rules",
                "• /start or /start N — start a round (N=1–7 consecutive rounds, 4–5 letter acronym)",
                "• /vote N — vote for submission N during voting (or /vote N in DM with AcroBot)",
                "• /score — leaderboard",
            ]
            help_content = "\n".join(help_lines)
            msg = Message(room_id=room_id, user_id=user_id, content=help_content, message_type="chat")
            db.session.add(msg)
            db.session.commit()
            _broadcast_new_message(room_id, msg.to_dict())
            return

        # /away [message] — Set away status and message; clear with /away. /dnd and /online set status.
        if content.lower().startswith("/away"):
            away_text = content[5:].strip()
            user.away_message = away_text or None
            if hasattr(user, "user_status"):
                user.user_status = "away" if away_text else "online"
            db.session.commit()
            if away_text:
                emote_content = f"is away: {away_text}"
            else:
                emote_content = "is no longer away"
            msg = Message(room_id=room_id, user_id=user_id, content=emote_content, message_type="emote")
            db.session.add(msg)
            db.session.commit()
            _broadcast_new_message(room_id, msg.to_dict())
            emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
            return

        # /dnd — Set Do Not Disturb status.
        if content.strip().lower() == "/dnd":
            if hasattr(user, "user_status"):
                user.user_status = "dnd"
                db.session.commit()
            msg = Message(room_id=room_id, user_id=user_id, content="is now Do Not Disturb", message_type="emote")
            db.session.add(msg)
            db.session.commit()
            _broadcast_new_message(room_id, msg.to_dict())
            emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
            return

        # /online — Clear away/dnd, back to online.
        if content.strip().lower() == "/online":
            if hasattr(user, "user_status"):
                user.user_status = "online"
                user.away_message = None
                db.session.commit()
            msg = Message(room_id=room_id, user_id=user_id, content="is back online", message_type="emote")
            db.session.add(msg)
            db.session.commit()
            _broadcast_new_message(room_id, msg.to_dict())
            emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
            return

        # /nick <name> — Set or clear display name (shown in chat). Any user.
        if content.lower().startswith("/nick "):
            nick = content[6:].strip()
            old_display = getattr(user, "display_name", None) or None
            if hasattr(user, "display_name"):
                user.display_name = nick[:80] if nick else None
                db.session.commit()
            emote_content = "is now known as " + (nick or user.username) if nick else "cleared display name"
            msg = Message(room_id=room_id, user_id=user_id, content=emote_content, message_type="emote")
            db.session.add(msg)
            db.session.commit()
            _broadcast_new_message(room_id, msg.to_dict())
            emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
            _post_system_event(f"{user.username} changed nick to " + (nick or "(cleared)"))
            return

        # /status <text> — Set or clear status line (shown in whois). Any user.
        if content.lower().startswith("/status "):
            status_text = content[8:].strip()
            if hasattr(user, "status_line"):
                user.status_line = status_text[:120] if status_text else None
                db.session.commit()
            emote_content = "set status: " + (status_text or "(cleared)") if status_text else "cleared status"
            msg = Message(room_id=room_id, user_id=user_id, content=emote_content, message_type="emote")
            db.session.add(msg)
            db.session.commit()
            _broadcast_new_message(room_id, msg.to_dict())
            return

        # /whois <username> — IRC-style whois: user info, last seen, shared rooms. Reply to requester only.
        if content.lower().startswith("/whois "):
            to_username = content[7:].strip()
            if not to_username:
                emit("error", {"message": "Usage: /whois username"})
                return
            target = _user_by_username(to_username)
            if not target:
                emit("whois_result", {"error": f"User '{to_username}' not found"})
                return
            online = target.id in _online_user_ids
            payload = {
                "username": target.username,
                "user_id": target.id,
                "created_at": _isoformat_utc(target.created_at),
                "online": online,
                "display_name": getattr(target, "display_name", None) or None,
                "status_line": getattr(target, "status_line", None) or None,
                "last_seen": _isoformat_utc(getattr(target, "last_seen", None)),
            }
            if online:
                for sid, uid in list(_sid_to_user_id.items()):
                    if uid == target.id:
                        payload["ip"] = _sid_to_remote_addr.get(sid)
                        connected_at = _sid_to_connected_at.get(sid)
                        payload["connected_at"] = connected_at
                        if connected_at:
                            payload["connected_seconds"] = int(time.time() - connected_at)
                        break
            else:
                payload["ip"] = None
                payload["connected_at"] = None
                payload["connected_seconds"] = None
            # Shared rooms: room names where target has sent at least one message
            room_ids = db.session.query(Message.room_id).filter_by(user_id=target.id).distinct().all()
            room_ids = [r[0] for r in room_ids]
            shared_rooms = [r.name for r in Room.query.filter(Room.id.in_(room_ids)).all()] if room_ids else []
            payload["shared_rooms"] = shared_rooms
            emit("whois_result", payload)
            return

        # /topic <content> — set channel topic (any user); broadcast topic_updated to room
        if content.lower().startswith("/topic "):
            topic_content = content[6:].strip()
            room_obj.topic = topic_content or None
            room_obj.topic_set_by_id = user_id
            room_obj.topic_set_at = datetime.utcnow()
            db.session.commit()
            room_obj = Room.query.get(room_id)  # refresh for to_dict
            payload = {
                "room_id": room_id,
                "room": room_obj.to_dict(),
                "set_by_username": user.username,
                "set_at": _isoformat_utc(room_obj.topic_set_at),
            }
            emit("topic_updated", payload, room=f"room_{room_id}")
            logger.info("User %s set topic in room %s", user.username, room_id)
            return

        # Acrophobia room: game commands and submissions (no user message saved)
        if room_obj.name == "Acrophobia":
            acrobot = User.query.filter_by(username="AcroBot").first()
            if acrobot:
                result = acrophobia_handle_message(room_id, user_id, user.username, content, from_dm=False)
                consumed = result[0]
                bot_replies = result[1]
                dm_replies = result[2] if len(result) > 2 else []
                if consumed:
                    # Echo only the message part (after "acrobot") to DM — recipient sees just the message, not the command
                    low = content.strip().lower()
                    if (low.startswith("/m acrobot ") or low.startswith("/msg acrobot ") or
                            low.startswith("/message acrobot ") or low.startswith("!acrobot ")):
                        idx = low.find("acrobot") + len("acrobot")
                        msg_part = content[idx:].strip() or "(no message)"
                        dm_room = _get_or_create_dm_room(user_id, acrobot.id)
                        user_dm_msg = Message(
                            room_id=dm_room.id,
                            user_id=user_id,
                            content=msg_part,
                            message_type="chat",
                        )
                        db.session.add(user_dm_msg)
                        db.session.commit()
                        _broadcast_new_message(dm_room.id, user_dm_msg.to_dict())
                    for text in bot_replies:
                        if text:
                            msg = Message(
                                room_id=room_id,
                                user_id=acrobot.id,
                                content=text,
                                message_type="chat",
                            )
                            db.session.add(msg)
                            db.session.commit()
                            _broadcast_new_message(room_id, msg.to_dict())
                    for target_user_id, dm_text in dm_replies:
                        if dm_text:
                            dm_room = _get_or_create_dm_room(target_user_id, acrobot.id)
                            dm_msg = Message(
                                room_id=dm_room.id,
                                user_id=acrobot.id,
                                content=dm_text,
                                message_type="chat",
                            )
                            db.session.add(dm_msg)
                            db.session.commit()
                            _broadcast_new_message(dm_room.id, dm_msg.to_dict())
                    if bot_replies and is_acrobot_active() and "**Acronym:" in (bot_replies[0] or ""):
                        _schedule_acrophobia_submit_timer(room_id)
                        emit("acrophobia_phase", acrophobia_get_phase_info(room_id), room=f"room_{room_id}")
                    return

        # /ping username — notify that user (no message saved)
        if content.lower().startswith("/ping "):
            to_username = content[6:].strip()
            if not to_username:
                emit("error", {"message": "Usage: /ping username"})
                return
            target = _user_by_username(to_username)
            if not target:
                emit("error", {"message": f"User '{to_username}' not found"})
                return
            payload = {
                "from_user_id": user_id,
                "from_username": user.username,
                "to_user_id": target.id,
                "to_username": target.username,
            }
            emit("user_pinged", payload, room=f"room_{room_id}")
            away_msg = getattr(target, "away_message", None)
            if away_msg:
                emit("away_message", {"from_username": target.username, "message": away_msg})
            logger.info("%s pinged %s in room %s", user.username, target.username, room_id)
            return

        # /m, /msg, /message acrobot or !acrobot in any room: echo to user's DM with AcroBot (do NOT show in channel)
        low_content = content.strip().lower()
        acrobot_in_any_room = (
            (low_content.startswith("/m acrobot ") or low_content.startswith("/msg acrobot ") or
             low_content.startswith("/message acrobot ") or low_content.startswith("!acrobot "))
            and room_obj.name != "Acrophobia"
        )
        if acrobot_in_any_room:
            acrobot = User.query.filter_by(username="AcroBot").first()
            if acrobot:
                idx = low_content.find("acrobot") + len("acrobot")
                msg_part = content.strip()[idx:].strip() or "(no message)"
                dm_room = _get_or_create_dm_room(user_id, acrobot.id)
                user_dm_msg = Message(
                    room_id=dm_room.id,
                    user_id=user_id,
                    content=msg_part,
                    message_type="chat",
                )
                db.session.add(user_dm_msg)
                db.session.commit()
                _broadcast_new_message(dm_room.id, user_dm_msg.to_dict())
                return

        # /em or /me text — third-person emote (saved as message_type='emote')
        message_type = "chat"
        if content.lower().startswith("/em "):
            content = content[4:].strip()
            message_type = "emote"
        elif content.lower().startswith("/me "):
            content = content[4:].strip()
            message_type = "emote"
        if message_type == "emote" and not content:
            emit("error", {"message": "Usage: /em your action"})
            return

        parent_id = None
        raw_parent_id = (data or {}).get("parent_id")
        if raw_parent_id is not None:
            try:
                pid = int(raw_parent_id)
                parent_msg = Message.query.filter_by(id=pid, room_id=room_id).first()
                if parent_msg:
                    parent_id = pid
            except (TypeError, ValueError):
                pass

        attachment_url = (data or {}).get("attachment_url") or None
        attachment_filename = (data or {}).get("attachment_filename") or None
        if attachment_url and not attachment_url.startswith("/uploads/"):
            attachment_url = None
            attachment_filename = None

        if not content and not attachment_url:
            emit("error", {"message": "Message or attachment required"})
            return

        link_previews_json = None
        if message_type == "chat":
            previews = get_previews_for_message_content(content, max_previews=3)
            if previews:
                link_previews_json = json.dumps(previews)

        msg = Message(
            room_id=room_id,
            user_id=user_id,
            content=content or "",
            message_type=message_type,
            parent_id=parent_id,
            attachment_url=attachment_url,
            attachment_filename=attachment_filename,
            link_previews=link_previews_json,
        )
        db.session.add(msg)
        db.session.commit()

        payload = msg.to_dict()
        _broadcast_new_message(room_id, payload)

        # @mention: parse @nickname and notify mentioned users (page)
        if message_type == "chat":
            mention_re = re.compile(r"@(\w+)", re.IGNORECASE)
            for match in mention_re.finditer(content):
                nick = match.group(1)
                target = _user_by_username(nick)
                if target and target.id != user_id:
                    for sid, uid in list(_sid_to_user_id.items()):
                        if uid == target.id:
                            socketio.emit(
                                "user_mentioned",
                                {
                                    "room_id": room_id,
                                    "message_id": msg.id,
                                    "from_user_id": user_id,
                                    "from_username": user.username,
                                    "content_snippet": (content[:80] + "…") if len(content) > 80 else content,
                                },
                                room=sid,
                            )
                            break

        logger.info("Message in room %s from %s", room_id, user.username)

    @socketio.on("edit_message")
    def on_edit_message(data):
        """Edit own message. Emit message_edited to room."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        msg_id = (data or {}).get("message_id")
        new_content = ((data or {}).get("content") or "").strip()
        if not msg_id or not new_content:
            emit("error", {"message": "message_id and content required"})
            return
        try:
            msg_id = int(msg_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid message_id"})
            return
        msg = Message.query.get(msg_id)
        if not msg:
            emit("error", {"message": "Message not found"})
            return
        if msg.user_id != user_id:
            emit("error", {"message": "You can only edit your own messages"})
            return
        msg.content = new_content
        msg.edited_at = datetime.utcnow()
        previews = get_previews_for_message_content(new_content, max_previews=3)
        msg.link_previews = json.dumps(previews) if previews else None
        db.session.commit()
        payload = msg.to_dict()
        emit("message_edited", payload, room=f"room_{msg.room_id}")
        logger.info("Message %s edited by user %s", msg_id, user_id)

    @socketio.on("delete_message")
    def on_delete_message(data):
        """Delete own message. Emit message_deleted to room."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        msg_id = (data or {}).get("message_id")
        if not msg_id:
            emit("error", {"message": "message_id required"})
            return
        try:
            msg_id = int(msg_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid message_id"})
            return
        msg = Message.query.get(msg_id)
        if not msg:
            emit("error", {"message": "Message not found"})
            return
        if msg.user_id != user_id:
            emit("error", {"message": "You can only delete your own messages"})
            return
        room_id = msg.room_id
        db.session.delete(msg)
        db.session.commit()
        emit("message_deleted", {"message_id": msg_id, "room_id": room_id}, room=f"room_{room_id}")
        logger.info("Message %s deleted by user %s", msg_id, user_id)

    @socketio.on("add_reaction")
    def on_add_reaction(data):
        """Add emoji reaction to message. Emit reaction_updated to room."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        msg_id = (data or {}).get("message_id")
        emoji = ((data or {}).get("emoji") or "").strip()
        if not msg_id or not emoji or len(emoji) > 32:
            emit("error", {"message": "message_id and emoji (1-32 chars) required"})
            return
        try:
            msg_id = int(msg_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid message_id"})
            return
        msg = Message.query.get(msg_id)
        if not msg:
            emit("error", {"message": "Message not found"})
            return
        existing = MessageReaction.query.filter_by(message_id=msg_id, user_id=user_id, emoji=emoji).first()
        if existing:
            return
        r = MessageReaction(message_id=msg_id, user_id=user_id, emoji=emoji)
        db.session.add(r)
        db.session.commit()
        msg = Message.query.get(msg_id)
        payload = {"message_id": msg_id, "room_id": msg.room_id, "reactions": msg.to_dict().get("reactions", [])}
        socketio.emit("reaction_updated", payload, room=f"room_{msg.room_id}")

    @socketio.on("remove_reaction")
    def on_remove_reaction(data):
        """Remove emoji reaction from message. Emit reaction_updated to room."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        msg_id = (data or {}).get("message_id")
        emoji = ((data or {}).get("emoji") or "").strip()
        if not msg_id or not emoji:
            emit("error", {"message": "message_id and emoji required"})
            return
        try:
            msg_id = int(msg_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid message_id"})
            return
        r = MessageReaction.query.filter_by(message_id=msg_id, user_id=user_id, emoji=emoji).first()
        if not r:
            return
        room_id = r.message.room_id
        db.session.delete(r)
        db.session.commit()
        msg = Message.query.get(msg_id)
        payload = {"message_id": msg_id, "room_id": room_id, "reactions": msg.to_dict().get("reactions", []) if msg else []}
        socketio.emit("reaction_updated", payload, room=f"room_{room_id}")

    @socketio.on("delete_my_messages")
    def on_delete_my_messages(data):
        """Delete all messages sent by the current user. Requires confirmation."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        confirm = (data or {}).get("confirm")
        if confirm != "DELETE_ALL_MY_MESSAGES":
            emit("error", {"message": "Confirmation required. Send confirm: DELETE_ALL_MY_MESSAGES"})
            return
        msgs = Message.query.filter_by(user_id=user_id).all()
        by_room = {}
        for m in msgs:
            by_room.setdefault(m.room_id, []).append(m.id)
        for m in msgs:
            db.session.delete(m)
        db.session.commit()
        for room_id, msg_ids in by_room.items():
            socketio.emit("messages_deleted", {"room_id": room_id, "message_ids": msg_ids}, room=f"room_{room_id}")
        emit("my_messages_deleted", {"deleted_count": len(msgs)})
        logger.info("User %s deleted all their messages (%d)", user_id, len(msgs))

    @socketio.on("set_message_retention")
    def on_set_message_retention(data):
        """Set auto-delete retention: null (never), 7, 30, or 90 days."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        user = User.query.get(user_id)
        if not user:
            emit("error", {"message": "User not found"})
            return
        val = (data or {}).get("days")
        if val is None or val == "" or val == "null":
            user.message_retention_days = None
        else:
            try:
                days = int(val)
                if days not in (7, 30, 90):
                    emit("error", {"message": "Retention must be 7, 30, or 90 days"})
                    return
                user.message_retention_days = days
            except (TypeError, ValueError):
                emit("error", {"message": "Invalid retention value"})
                return
        db.session.commit()
        emit("message_retention_updated", {"days": user.message_retention_days})

    @socketio.on("report_message")
    def on_report_message(data):
        """Report a message (App Store compliance). One report per user per message."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        msg_id = (data or {}).get("message_id")
        reason = ((data or {}).get("reason") or "").strip() or None
        if not msg_id:
            emit("error", {"message": "message_id required"})
            return
        try:
            msg_id = int(msg_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid message_id"})
            return
        msg = Message.query.get(msg_id)
        if not msg:
            emit("error", {"message": "Message not found"})
            return
        existing = MessageReport.query.filter_by(message_id=msg_id, reported_by_user_id=user_id).first()
        if existing:
            emit("report_submitted", {"ok": True, "message": "You have already reported this message."})
            return
        report = MessageReport(message_id=msg_id, reported_by_user_id=user_id, reason=reason)
        db.session.add(report)
        db.session.commit()
        emit("report_submitted", {"ok": True, "message": "Report submitted. Thank you."})
        logger.info("Message %s reported by user %s", msg_id, user_id)

    @socketio.on("mute_user_in_room")
    def on_mute_user_in_room(data):
        """Mute a user in the current room. Emit room_muted_updated to requester."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        room_id = (data or {}).get("room_id")
        muted_user_id = (data or {}).get("muted_user_id")
        if not room_id or not muted_user_id:
            emit("error", {"message": "room_id and muted_user_id required"})
            return
        try:
            room_id = int(room_id)
            muted_user_id = int(muted_user_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid room_id or muted_user_id"})
            return
        if muted_user_id == user_id:
            emit("error", {"message": "You cannot mute yourself"})
            return
        room = Room.query.get(room_id)
        if not room:
            emit("error", {"message": "Room not found"})
            return
        existing = RoomMute.query.filter_by(room_id=room_id, muted_user_id=muted_user_id, muted_by_id=user_id).first()
        if existing:
            emit("room_muted_updated", {"room_id": room_id, "room_muted_in_room": list(_get_room_mutes_for_user(user_id, room_id))})
            return
        m = RoomMute(room_id=room_id, muted_user_id=muted_user_id, muted_by_id=user_id)
        db.session.add(m)
        db.session.commit()
        emit("room_muted_updated", {"room_id": room_id, "room_muted_in_room": list(_get_room_mutes_for_user(user_id, room_id))})
        logger.info("User %s muted user %s in room %s", user_id, muted_user_id, room_id)

    @socketio.on("unmute_user_in_room")
    def on_unmute_user_in_room(data):
        """Unmute a user in the current room. Emit room_muted_updated to requester."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        room_id = (data or {}).get("room_id")
        muted_user_id = (data or {}).get("muted_user_id")
        if not room_id or not muted_user_id:
            emit("error", {"message": "room_id and muted_user_id required"})
            return
        try:
            room_id = int(room_id)
            muted_user_id = int(muted_user_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid room_id or muted_user_id"})
            return
        RoomMute.query.filter_by(room_id=room_id, muted_user_id=muted_user_id, muted_by_id=user_id).delete()
        db.session.commit()
        emit("room_muted_updated", {"room_id": room_id, "room_muted_in_room": list(_get_room_mutes_for_user(user_id, room_id))})
        logger.info("User %s unmuted user %s in room %s", user_id, muted_user_id, room_id)

    @socketio.on("search_messages")
    def on_search_messages(data):
        """Search messages in a room (or all rooms). Returns search_results with list of message dicts."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        query = ((data or {}).get("query") or "").strip()
        if not query or len(query) < 1:
            emit("search_results", {"messages": [], "query": query or ""})
            return
        room_id = (data or {}).get("room_id")
        try:
            if room_id is not None:
                room_id = int(room_id)
        except (TypeError, ValueError):
            room_id = None
        exclude_set = set()
        if room_id is not None:
            exclude_set = _get_room_mutes_for_user(user_id, room_id)
        q = Message.query.filter(Message.message_type == "chat")
        if room_id is not None:
            q = q.filter(Message.room_id == room_id)
        if exclude_set:
            q = q.filter(~Message.user_id.in_(exclude_set))
        q = q.filter(Message.content.ilike(f"%{query}%"))
        messages = q.order_by(Message.created_at.desc()).limit(50).all()
        room_ids = {m.room_id for m in messages}
        rooms_by_id = {r.id: r for r in Room.query.filter(Room.id.in_(room_ids)).all()} if room_ids else {}
        results = []
        for m in messages:
            d = m.to_dict()
            d["room_name"] = rooms_by_id.get(m.room_id).name if rooms_by_id.get(m.room_id) else None
            results.append(d)
        emit("search_results", {"messages": results, "query": query})

    @socketio.on("create_room")
    def on_create_room(data):
        """Create a new room. Super Admin only. Broadcast rooms_updated to all."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _has_permission(user_id, "create_room"):
            emit("error", {"message": "Only Surfer Girls can create channels (or your role needs this permission)"})
            return
        name = ((data or {}).get("name") or "").strip()
        if not name:
            emit("error", {"message": "Room name required"})
            return
        if Room.query.filter_by(name=name).first():
            emit("error", {"message": "A room with that name already exists"})
            return
        room = Room(name=name, created_by_id=user_id)
        db.session.add(room)
        db.session.commit()
        _audit_log(user_id, "create_room", "room", room.id, {"name": name})
        rooms = Room.query.order_by(Room.name).all()
        emit("rooms_updated", {"rooms": [r.to_dict() for r in rooms]}, broadcast=True)
        emit("room_created", {"room": room.to_dict()})
        logger.info("Room created: %s by user %s", name, user_id)

    @socketio.on("update_room")
    def on_update_room(data):
        """Rename a room. Super Admin or room owner. Broadcast rooms_updated to all."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        room_id = (data or {}).get("room_id")
        name = ((data or {}).get("name") or "").strip()
        if not room_id:
            emit("error", {"message": "room_id required"})
            return
        try:
            room_id = int(room_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid room_id"})
            return
        room = Room.query.get(room_id)
        if not room:
            emit("error", {"message": "Room not found"})
            return
        is_owner = room.created_by_id == user_id
        if not _has_permission(user_id, "update_room") and not is_owner:
            emit("error", {"message": "Only Surfer Girls, room owners, or users with edit permission can edit channels"})
            return
        changed = False
        if name:
            if Room.query.filter(Room.name == name, Room.id != room_id).first():
                emit("error", {"message": "A room with that name already exists"})
                return
            room.name = name
            changed = True
        if _is_super_admin(user_id) and "is_protected" in (data or {}):
            new_val = bool((data or {}).get("is_protected"))
            if room.is_protected != new_val:
                room.is_protected = new_val
                changed = True
        if not changed:
            emit("error", {"message": "No changes to apply"})
            return
        db.session.commit()
        _audit_log(user_id, "update_room", "room", room_id, {"name": name, "is_protected": getattr(room, "is_protected", None)})
        rooms = Room.query.order_by(Room.name).all()
        emit("rooms_updated", {"rooms": [r.to_dict() for r in rooms]}, broadcast=True)
        emit("room_renamed", {"room_id": room_id, "room": room.to_dict()})
        logger.info("Room updated: %s -> %s", room_id, name)

    @socketio.on("delete_room")
    def on_delete_room(data):
        """Delete a room and its messages. Super Admin or room owner. Broadcast rooms_updated to all."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        room_id = (data or {}).get("room_id")
        if not room_id:
            emit("error", {"message": "room_id required"})
            return
        try:
            room_id = int(room_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid room_id"})
            return
        room = Room.query.get(room_id)
        if not room:
            emit("error", {"message": "Room not found"})
            return
        is_owner = room.created_by_id == user_id or (room.dm_with_id and room.dm_with_id == user_id)
        if not _has_permission(user_id, "delete_room") and not is_owner:
            emit("error", {"message": "Only Surfer Girls, room owners, or users with delete permission can delete channels"})
            return
        general = Room.query.filter_by(name="general").first()
        if general and room.id == general.id:
            emit("error", {"message": "Cannot delete the general room"})
            return
        if getattr(room, "is_protected", False):
            if not (data or {}).get("from_settings"):
                emit("error", {"message": "Protected channels can only be removed via Settings by a Surfer Girl"})
                return
            if not _is_super_admin(user_id):
                emit("error", {"message": "Only Surfer Girls can delete protected channels"})
                return
        room_name = room.name
        db.session.delete(room)
        db.session.commit()
        _audit_log(user_id, "delete_room", "room", room_id, {"name": room_name})
        rooms = Room.query.order_by(Room.name).all()
        emit("rooms_updated", {"rooms": [r.to_dict() for r in rooms]}, broadcast=True)
        emit("room_deleted", {"room_id": room_id})
        logger.info("Room deleted: %s", room_id)

    @socketio.on("wipe_room_history")
    def on_wipe_room_history(data):
        """Delete all messages in a room. Super Admin only."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _is_super_admin(user_id):
            emit("error", {"message": "Only Surfer Girls can wipe room history"})
            return
        room_id = (data or {}).get("room_id")
        if not room_id:
            emit("error", {"message": "room_id required"})
            return
        try:
            room_id = int(room_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid room_id"})
            return
        room = Room.query.get(room_id)
        if not room:
            emit("error", {"message": "Room not found"})
            return
        room_name = room.name
        deleted = Message.query.filter_by(room_id=room_id).delete()
        db.session.commit()
        _audit_log(user_id, "wipe_room_history", "room", room_id, {"name": room_name, "deleted": deleted})
        emit("room_history_wiped", {"room_id": room_id, "deleted": deleted})
        logger.info("Room %s history wiped: %s messages deleted by user %s", room_id, deleted, user_id)

    @socketio.on("save_room_order")
    def on_save_room_order(data):
        """Save user's room order (list of room_ids)."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        room_ids = (data or {}).get("room_ids") or []
        try:
            room_ids = [int(x) for x in room_ids]
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid room_ids"})
            return
        user = User.query.get(user_id)
        if not user:
            return
        user.room_order_ids = json.dumps(room_ids)
        db.session.commit()
        rooms = _rooms_sorted_for_user(user_id)
        unread_counts = _get_unread_counts(user_id)
        emit("rooms_list", {"rooms": [r.to_dict() for r in rooms], "unread_counts": unread_counts})

    @socketio.on("get_user_profile")
    def on_get_user_profile(data):
        """Return user dict (id, username, created_at) for view profile."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        target_id = (data or {}).get("user_id")
        if not target_id:
            return
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            return
        user = User.query.get(target_id)
        if user:
            emit("user_profile", {"user": user.to_dict()})

    @socketio.on("get_whois")
    def on_get_whois(data):
        """Return whois_result payload for a user (by user_id). Used from message context menu."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        target_id = (data or {}).get("user_id")
        if not target_id:
            return
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            return
        target = User.query.get(target_id)
        if not target:
            emit("whois_result", {"error": "User not found"})
            return
        online = target.id in _online_user_ids
        payload = {
            "username": target.username,
            "user_id": target.id,
            "created_at": _isoformat_utc(target.created_at),
            "online": online,
            "display_name": getattr(target, "display_name", None) or None,
            "status_line": getattr(target, "status_line", None) or None,
            "last_seen": _isoformat_utc(getattr(target, "last_seen", None)),
        }
        if online:
            for sid, uid in list(_sid_to_user_id.items()):
                if uid == target.id:
                    payload["ip"] = _sid_to_remote_addr.get(sid)
                    connected_at = _sid_to_connected_at.get(sid)
                    payload["connected_at"] = connected_at
                    if connected_at:
                        payload["connected_seconds"] = int(time.time() - connected_at)
                    break
        else:
            payload["ip"] = None
            payload["connected_at"] = None
            payload["connected_seconds"] = None
        room_ids = db.session.query(Message.room_id).filter_by(user_id=target.id).distinct().all()
        room_ids = [r[0] for r in room_ids]
        payload["shared_rooms"] = [r.name for r in Room.query.filter(Room.id.in_(room_ids)).all()] if room_ids else []
        emit("whois_result", payload)

    @socketio.on("get_or_create_dm")
    def on_get_or_create_dm(data):
        """Get or create a DM room with another user. Return room and broadcast rooms_updated if created."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        other_id = (data or {}).get("other_user_id")
        if not other_id:
            emit("error", {"message": "other_user_id required"})
            return
        try:
            other_id = int(other_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid other_user_id"})
            return
        if other_id == user_id:
            emit("error", {"message": "Cannot DM yourself"})
            return
        other = User.query.get(other_id)
        if not other:
            emit("error", {"message": "User not found"})
            return
        # Find existing DM room between the two users
        room = Room.query.filter(
            or_(
                and_(Room.created_by_id == user_id, Room.dm_with_id == other_id),
                and_(Room.created_by_id == other_id, Room.dm_with_id == user_id),
            ),
        ).first()
        if not room:
            room = Room(name="DM", created_by_id=user_id, dm_with_id=other_id)
            db.session.add(room)
            db.session.commit()
            rooms = Room.query.order_by(Room.name).all()
            emit("rooms_updated", {"rooms": [r.to_dict() for r in rooms]}, broadcast=True)
            logger.info("DM room created between %s and %s", user_id, other_id)
        emit("dm_room", {"room": room.to_dict()})

    @socketio.on("kick_user")
    def on_kick_user(data):
        """Emit kicked_from_room to target user's socket(s). Super Admin only."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _has_permission(user_id, "kick_user"):
            emit("error", {"message": "Only Surfer Girls can kick users (or your role needs this permission)"})
            return
        room_id = (data or {}).get("room_id")
        target_id = (data or {}).get("target_user_id")
        if not room_id or not target_id:
            emit("error", {"message": "room_id and target_user_id required"})
            return
        try:
            room_id = int(room_id)
            target_id = int(target_id)
        except (TypeError, ValueError):
            return
        if target_id == user_id:
            emit("error", {"message": "Cannot kick yourself"})
            return
        room = Room.query.get(room_id)
        if not room:
            return
        target_user = User.query.get(target_id)
        target_username = target_user.username if target_user else str(target_id)
        _audit_log(user_id, "kick_user", "user", target_id, {"room_id": room_id, "target_username": target_username})
        for sid, uid in list(_sid_to_user_id.items()):
            if uid == target_id:
                socketio.emit("kicked_from_app", {"message": "You were kicked from the app."}, room=sid)
                socketio_disconnect(sid)
                logger.info("User %s kicked user %s out of the app", user_id, target_id)
                break

    @socketio.on("set_super_admin")
    def on_set_super_admin(data):
        """Set or unset Super Admin for a user. Caller must be Super Admin. Broadcast user_list_updated."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _is_super_admin(user_id):
            emit("error", {"message": "Only Surfer Girls can assign Surfer Girl"})
            return
        target_id = (data or {}).get("target_user_id")
        is_super = (data or {}).get("is_super_admin")
        if target_id is None:
            emit("error", {"message": "target_user_id required"})
            return
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid target_user_id"})
            return
        target = User.query.get(target_id)
        if not target:
            emit("error", {"message": "User not found"})
            return
        target.is_super_admin = bool(is_super)
        db.session.commit()
        _audit_log(user_id, "set_super_admin", "user", target_id, {"target_username": target.username, "is_super_admin": target.is_super_admin})
        emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
        logger.info("User %s set Super Admin for user %s to %s", user_id, target_id, target.is_super_admin)

    @socketio.on("set_user_rank")
    def on_set_user_rank(data):
        """Set a user's rank (rookie, bro, fam, super_admin). Caller must be Super Admin. Broadcast user_list_updated."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _has_permission(user_id, "set_user_rank"):
            emit("error", {"message": "Only Surfer Girls can set user rankings (or your role needs this permission)"})
            return
        target_id = (data or {}).get("target_user_id")
        rank = ((data or {}).get("rank") or "").strip().lower()
        if target_id is None:
            emit("error", {"message": "target_user_id required"})
            return
        if rank not in ("rookie", "bro", "fam", "super_admin"):
            emit("error", {"message": "rank must be one of: rookie, bro, fam, super_admin"})
            return
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid target_user_id"})
            return
        target = User.query.get(target_id)
        if not target:
            emit("error", {"message": "User not found"})
            return
        target.rank = rank
        target.is_super_admin = rank == "super_admin"
        db.session.commit()
        _audit_log(user_id, "set_user_rank", "user", target_id, {"target_username": target.username, "rank": rank})
        emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
        logger.info("User %s set rank for user %s to %s", user_id, target_id, rank)

    @socketio.on("delete_user")
    def on_delete_user(data):
        """Delete a user permanently. Surfer Girl only. Disconnects target if online."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _is_super_admin(user_id):
            emit("error", {"message": "Only Surfer Girls can delete users"})
            return
        target_id = (data or {}).get("target_user_id")
        if target_id is None:
            emit("error", {"message": "target_user_id required"})
            return
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid target_user_id"})
            return
        if target_id == user_id:
            emit("error", {"message": "Cannot delete yourself; use Delete my account in Settings"})
            return
        target = User.query.get(target_id)
        if not target:
            emit("error", {"message": "User not found"})
            return
        if target.username in ("AcroBot", "System", "Homer"):
            emit("error", {"message": "Cannot delete system users"})
            return
        target_username = target.username
        # Disconnect target if online
        for sid, uid in list(_sid_to_user_id.items()):
            if uid == target_id:
                socketio.emit("kicked_from_app", {"message": "Your account was deleted."}, room=sid)
                socketio_disconnect(sid)
                break
        # Cascade delete: reports by user, reports of user's messages, ignore list, room refs
        msg_ids = [r[0] for r in db.session.query(Message.id).filter_by(user_id=target_id).all()]
        if msg_ids:
            MessageReport.query.filter(MessageReport.message_id.in_(msg_ids)).delete(synchronize_session=False)
        MessageReport.query.filter_by(reported_by_user_id=target_id).delete()
        IgnoreList.query.filter(
            (IgnoreList.user_id == target_id) | (IgnoreList.ignored_user_id == target_id)
        ).delete(synchronize_session=False)
        Message.query.filter_by(user_id=target_id).delete()
        Room.query.filter(Room.created_by_id == target_id).update({"created_by_id": None})
        Room.query.filter(Room.topic_set_by_id == target_id).update({"topic_set_by_id": None})
        Room.query.filter(Room.dm_with_id == target_id).update({"dm_with_id": None})
        RoomMute.query.filter(
            (RoomMute.muted_user_id == target_id) | (RoomMute.muted_by_id == target_id)
        ).delete(synchronize_session=False)
        AcroScore.query.filter_by(user_id=target_id).delete()
        db.session.delete(target)
        db.session.commit()
        _audit_log(user_id, "delete_user", "user", target_id, {"target_username": target_username})
        emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
        emit("rooms_updated", {"rooms": [r.to_dict() for r in _rooms_sorted_for_user(user_id)]}, broadcast=True)
        logger.info("User %s deleted user %s", user_id, target_id)

    @socketio.on("get_role_permissions")
    def on_get_role_permissions(data=None):
        """Return role permissions for Settings. Surfer Girl only."""
        user_id = session.get("user_id")
        if not user_id:
            emit("role_permissions", {"permissions": {}, "default_room_id": None})
            return
        if not _is_super_admin(user_id):
            emit("role_permissions", {"permissions": {}, "default_room_id": None})
            return
        default_rid = _get_default_room_id()
        emit("role_permissions", {"permissions": _get_role_permissions_dict(), "default_room_id": default_rid})

    @socketio.on("get_audit_log")
    def on_get_audit_log(data=None):
        """Return recent audit log entries. Surfer Girl only."""
        user_id = session.get("user_id")
        if not user_id:
            emit("audit_log", {"entries": []})
            return
        if not _is_super_admin(user_id):
            emit("audit_log", {"entries": []})
            return
        limit = min(100, max(10, int((data or {}).get("limit", 50))))
        entries = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        emit("audit_log", {"entries": [e.to_dict() for e in entries]})

    @socketio.on("set_default_room")
    def on_set_default_room(data):
        """Set default channel for login. Surfer Girl only."""
        user_id = session.get("user_id")
        if not user_id or not _is_super_admin(user_id):
            emit("error", {"message": "Only Surfer Girls can set the default channel"})
            return
        room_id = (data or {}).get("room_id")
        if room_id is None:
            emit("error", {"message": "room_id required"})
            return
        try:
            room_id = int(room_id)
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid room_id"})
            return
        room = Room.query.get(room_id)
        if not room or room.dm_with_id:
            emit("error", {"message": "Room not found or cannot be default (DMs not allowed)"})
            return
        row = AppSetting.query.filter_by(key="default_room_id").first()
        if row:
            row.value = str(room_id)
        else:
            db.session.add(AppSetting(key="default_room_id", value=str(room_id)))
        db.session.commit()
        _audit_log(user_id, "set_default_room", "room", room_id, {"room_name": room.name})
        emit("default_room_updated", {"default_room_id": room_id})
        logger.info("User %s set default room to %s", user_id, room_id)

    @socketio.on("set_role_permission")
    def on_set_role_permission(data):
        """Set a permission for a role. Surfer Girl only."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _is_super_admin(user_id):
            emit("error", {"message": "Only Surfer Girls can configure role permissions"})
            return
        role = ((data or {}).get("role") or "").strip().lower()
        permission = ((data or {}).get("permission") or "").strip()
        allowed = (data or {}).get("allowed")
        if role not in ("rookie", "bro", "fam"):
            emit("error", {"message": "role must be rookie, bro, or fam"})
            return
        valid_perms = ("create_room", "update_room", "delete_room", "kick_user", "set_user_rank", "acrobot_control", "homer_control", "reset_stats", "export_all")
        if permission not in valid_perms:
            emit("error", {"message": f"permission must be one of: {', '.join(valid_perms)}"})
            return
        rp = RolePermission.query.filter_by(role=role, permission=permission).first()
        if rp:
            rp.allowed = bool(allowed)
        else:
            db.session.add(RolePermission(role=role, permission=permission, allowed=bool(allowed)))
        db.session.commit()
        _audit_log(user_id, "set_role_permission", None, None, {"role": role, "permission": permission, "allowed": bool(allowed)})
        emit("role_permissions", {"permissions": _get_role_permissions_dict()})
        logger.info("User %s set %s.%s = %s", user_id, role, permission, allowed)

    @socketio.on("get_acrobot_status")
    def on_get_acrobot_status(data=None):
        """Return whether AcroBot is active (online). Any user can request."""
        emit("acrobot_status", {"active": is_acrobot_active()})

    @socketio.on("set_acrobot_active")
    def on_set_acrobot_active(data):
        """Activate or deactivate AcroBot. Super Admin only. Broadcast acrobot_status."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _has_permission(user_id, "acrobot_control"):
            emit("error", {"message": "Only Surfer Girls can activate or deactivate AcroBot (or your role needs this permission)"})
            return
        active = (data or {}).get("active")
        if active is None:
            emit("error", {"message": "active (true/false) required"})
            return
        acrophobia_set_acrobot_active(bool(active))
        _audit_log(user_id, "set_acrobot_active", None, None, {"active": is_acrobot_active()})
        emit("acrobot_status", {"active": is_acrobot_active()}, broadcast=True)
        emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
        logger.info("User %s set AcroBot active=%s", user_id, is_acrobot_active())

    @socketio.on("get_homer_status")
    def on_get_homer_status(data=None):
        """Return whether Homer is active (online). Any user can request."""
        emit("homer_status", {"active": is_homer_active()})

    @socketio.on("set_homer_active")
    def on_set_homer_active(data):
        """Activate or deactivate Homer. Surfer Girl or homer_control permission."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _has_permission(user_id, "homer_control"):
            emit("error", {"message": "Only Surfer Girls can activate or deactivate Homer (or your role needs homer_control permission)"})
            return
        active = (data or {}).get("active")
        if active is None:
            emit("error", {"message": "active (true/false) required"})
            return
        homer_set_active(bool(active))
        _audit_log(user_id, "set_homer_active", None, None, {"active": is_homer_active()})
        emit("homer_status", {"active": is_homer_active()}, broadcast=True)
        emit("user_list_updated", {"users": _get_users_with_online_status()}, broadcast=True)
        logger.info("User %s set Homer active=%s", user_id, is_homer_active())

    @socketio.on("reset_stats_data")
    def on_reset_stats_data(data):
        """Delete all messages (resets Stats channel data). Super Admin only. Requires confirm key."""
        user_id = session.get("user_id")
        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return
        if not _has_permission(user_id, "reset_stats"):
            emit("error", {"message": "Only Surfer Girls can reset Stats data (or your role needs this permission)"})
            return
        if (data or {}).get("confirm") != "RESET":
            emit("error", {"message": "Send confirm: 'RESET' to reset all message data (Stats). This cannot be undone."})
            return
        deleted = Message.query.delete()
        db.session.commit()
        _audit_log(user_id, "reset_stats_data", None, None, {"deleted": deleted})
        emit("stats_reset", {"deleted": deleted})
        logger.info("User %s reset Stats data: %s messages deleted", user_id, deleted)
