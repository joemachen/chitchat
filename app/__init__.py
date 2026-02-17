# ChitChat application package
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash

from app.models import AppSetting, Message, Room, RoomAlias, RoomMember, User, db
from app.version import VERSION

logger = logging.getLogger("chitchat")


def _get_release_notes_for_version(version: str) -> str | None:
    """Load release notes for the given version from RELEASE_NOTES.md. Returns None if not found."""
    try:
        root = Path(__file__).resolve().parent.parent
        notes_path = root / "RELEASE_NOTES.md"
        if not notes_path.exists():
            return None
        text = notes_path.read_text(encoding="utf-8")
        ver = version.lstrip("v")  # "1.1.0"
        target = f"v{ver}"  # "v1.1.0"
        lines = text.splitlines()
        in_section = False
        collected = []
        for line in lines:
            if line.strip().startswith("## "):
                parts = line.split()
                if len(parts) >= 2 and (parts[1] == target or parts[1].lstrip("v") == ver):
                    in_section = True
                    continue
                if in_section:
                    break
            if in_section:
                if line.strip() == "---":
                    break
                collected.append(line)
        return "\n".join(collected).strip() if collected else None
    except Exception as e:
        logger.debug("Could not load release notes: %s", e)
        return None


def _post_deploy_announcement(app: Flask) -> None:
    """Post server deploy announcement to System Events only when version has changed."""
    with app.app_context():
        try:
            row = AppSetting.query.filter_by(key="last_deploy_announced_version").first()
            last_announced = row.value if row and row.value else None
            if last_announced == VERSION:
                logger.debug("Skipping deploy announcement: version %s already announced", VERSION)
                return

            sys_room = Room.query.filter_by(name="System Events").first()
            sys_user = User.query.filter_by(username="System").first()
            if sys_room and sys_user:
                header = f"Server redeployed (v{VERSION})"
                notes = _get_release_notes_for_version(VERSION)
                content = f"{header}\n\n{notes}" if notes else header
                msg = Message(
                    room_id=sys_room.id,
                    user_id=sys_user.id,
                    content=content,
                    message_type="chat",
                )
                db.session.add(msg)
                if row:
                    row.value = VERSION
                else:
                    db.session.add(AppSetting(key="last_deploy_announced_version", value=VERSION))
                db.session.commit()
                logger.info("Posted deploy announcement v%s", VERSION)
        except Exception as e:
            logger.warning("Deploy announcement skipped: %s", e)


def _run_message_retention_cleanup(app: Flask) -> None:
    """Delete messages for users who have message_retention_days set and messages older than that."""
    with app.app_context():
        try:
            users_with_retention = User.query.filter(User.message_retention_days.isnot(None)).all()
            cutoff = datetime.utcnow()
            total_deleted = 0
            for u in users_with_retention:
                days = u.message_retention_days
                if not days or days <= 0:
                    continue
                threshold = cutoff - timedelta(days=days)
                deleted = Message.query.filter(
                    Message.user_id == u.id,
                    Message.created_at < threshold,
                ).delete()
                if deleted:
                    total_deleted += deleted
            if total_deleted:
                db.session.commit()
                logger.info("Message retention cleanup: deleted %d old messages", total_deleted)
        except Exception as e:
            logger.warning("Message retention cleanup skipped: %s", e)
            db.session.rollback()


def _seed_default_data(app: Flask) -> None:
    """
    Ensure default rooms and system users exist. Safe to run multiple times.
    Call after migrations (e.g. from run.py or after flask db upgrade).
    """
    with app.app_context():
        try:
            # Only create "general" if there are no channels at all (user may have renamed it)
            has_any_channel = Room.query.filter(Room.dm_with_id.is_(None)).first()
            if not has_any_channel:
                db.session.add(Room(name="general", is_protected=True))
                db.session.commit()
            for rname in ("Stats", "Acrophobia", "System Events", "Trivia"):
                r = Room.query.filter_by(name=rname).first()
                if not r:
                    db.session.add(Room(name=rname, is_protected=True))
                    db.session.commit()

            acrobot = User.query.filter_by(username="AcroBot").first()
            if not acrobot:
                acrobot = User(
                    username="AcroBot",
                    password_hash=generate_password_hash("system-bot-no-login"),
                )
                db.session.add(acrobot)
                db.session.commit()
            system_user = User.query.filter_by(username="System").first()
            if not system_user:
                system_user = User(
                    username="System",
                    password_hash=generate_password_hash("system-bot-no-login"),
                )
                db.session.add(system_user)
                db.session.commit()
            homer = User.query.filter_by(username="Homer").first()
            homer_status = "It says no HomerS. We're allowed to have one."
            if not homer:
                homer = User(
                    username="Homer",
                    password_hash=generate_password_hash("system-bot-no-login"),
                    status_line=homer_status,
                )
                db.session.add(homer)
                db.session.commit()
            elif getattr(homer, "status_line", None) != homer_status:
                homer.status_line = homer_status
                db.session.commit()
            prof_frink = User.query.filter_by(username="Prof Frink").first()
            frink_status = "Glavin! The mathematics of trivia await!"
            if not prof_frink:
                prof_frink = User(
                    username="Prof Frink",
                    password_hash=generate_password_hash("system-bot-no-login"),
                    status_line=frink_status,
                )
                db.session.add(prof_frink)
                db.session.commit()
            elif getattr(prof_frink, "status_line", None) != frink_status:
                prof_frink.status_line = frink_status
                db.session.commit()

            # Promote user "Joe" or "Joe-test" to Super Admin if present
            for username in ("Joe", "Joe-test"):
                user = User.query.filter_by(username=username).first()
                if user and not getattr(user, "is_super_admin", False):
                    user.is_super_admin = True
                    if hasattr(user, "rank"):
                        user.rank = "super_admin"
                    db.session.commit()

            # Room roles: backfill RoomMember for rooms with created_by_id
            if hasattr(db, "session"):
                try:
                    from app.room_roles import add_room_member
                    for room in Room.query.filter(Room.created_by_id.isnot(None), Room.dm_with_id.is_(None)).all():
                        if not RoomMember.query.filter_by(room_id=room.id, user_id=room.created_by_id).first():
                            add_room_member(room.id, room.created_by_id, "owner")
                except Exception:
                    pass  # Tables may not exist yet (pre-migration)

            # Room aliases: seed default aliases for known rooms
            try:
                from app.room_aliases import set_room_alias
                for rname, alias in [("general", "general"), ("Acrophobia", "acrophobia"), ("Trivia", "trivia"), ("Stats", "stats"), ("System Events", "system")]:
                    r = Room.query.filter_by(name=rname).first()
                    if r and r.dm_with_id is None:
                        set_room_alias(r.id, alias)
            except Exception:
                pass
        except Exception as e:
            logger.warning("Seed default data skipped or partial: %s", e)
            db.session.rollback()


# Keep socketio in module scope so run.py can use it
socketio = None


def create_app() -> Flask:
    """Application factory: db, Migrate, routes, socketio. No schema creation or upgrade here."""
    global socketio

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object("app.config.Config")

    # Trust X-Forwarded-* headers when behind Koyeb/nginx reverse proxy (required for WebSocket + cookies)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    try:
        db.init_app(app)
    except Exception as e:
        if "Could not parse SQLAlchemy URL" in str(e):
            raise RuntimeError(
                "Invalid database URL. Set DATABASE_URL or CHITCHAT_DATABASE_URI in Koyeb → "
                "Service → Environment variables to your Neon connection string "
                "(e.g. postgresql://user:password@host/dbname). "
                "Get the string from Neon Console → Connection details."
            ) from e
        raise

    from flask_migrate import Migrate
    Migrate(app, db)

    # Run migrations (and seed) on every app load so end users never need to run "flask db upgrade"
    # Skip when gunicorn_run already ran maintenance (faster startup for Koyeb health checks)
    if not os.environ.get("CHITCHAT_MAINTENANCE_DONE"):
        with app.app_context():
            try:
                from flask_migrate import upgrade
                upgrade()
                _seed_default_data(app)
                _run_message_retention_cleanup(app)
                _post_deploy_announcement(app)
            except Exception as e:
                logger.exception("Migrations/seed on startup failed: %s", e)
                raise RuntimeError(
                    f"Database migrations failed: {e}. Run 'flask db upgrade' manually, or fix the error above."
                ) from e

    from app.routes import register_routes
    register_routes(app)

    _polling_only = app.config.get("SOCKET_POLLING_ONLY", False)
    socketio = SocketIO(
        app,
        async_mode="gevent",
        cors_allowed_origins="*" if _polling_only else [],
        logger=False,
        engineio_logger=False,
        allow_upgrade=not _polling_only,
    )
    from app.sockets import register_socket_handlers
    register_socket_handlers(socketio)

    app.socketio = socketio
    return app
