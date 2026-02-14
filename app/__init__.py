# ChitChat application package
import logging
from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash

from app.models import Room, User, db

logger = logging.getLogger("chitchat")


def _seed_default_data(app: Flask) -> None:
    """
    Ensure default rooms and system users exist. Safe to run multiple times.
    Call after migrations (e.g. from run.py or after flask db upgrade).
    """
    with app.app_context():
        try:
            general = Room.query.filter_by(name="general").first()
            if not general:
                general = Room(name="general")
                db.session.add(general)
                db.session.commit()
            stats_room = Room.query.filter_by(name="Stats").first()
            if not stats_room:
                db.session.add(Room(name="Stats"))
                db.session.commit()
            acrophobia_room = Room.query.filter_by(name="Acrophobia").first()
            if not acrophobia_room:
                db.session.add(Room(name="Acrophobia"))
                db.session.commit()
            system_events_room = Room.query.filter_by(name="System Events").first()
            if not system_events_room:
                db.session.add(Room(name="System Events"))
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

            # Promote user "Joe" to Super Admin if present
            joe = User.query.filter_by(username="Joe").first()
            if joe and not getattr(joe, "is_super_admin", False):
                joe.is_super_admin = True
                if hasattr(joe, "rank"):
                    joe.rank = "super_admin"
                db.session.commit()
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
    with app.app_context():
        try:
            from flask_migrate import upgrade
            upgrade()
            _seed_default_data(app)
        except Exception as e:
            logger.exception("Migrations/seed on startup failed: %s", e)
            raise RuntimeError(
                f"Database migrations failed: {e}. Run 'flask db upgrade' manually, or fix the error above."
            ) from e

    from app.routes import register_routes
    register_routes(app)

    socketio = SocketIO(
        app,
        async_mode="eventlet",
        cors_allowed_origins=[],
        logger=False,
        engineio_logger=False,
    )
    from app.sockets import register_socket_handlers
    register_socket_handlers(socketio)

    app.socketio = socketio
    return app
