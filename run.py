"""
ChitChat entry point. Validates environment, initializes logging, runs migrations, seeds data, starts the app.
For Flask CLI (e.g. flask db upgrade): FLASK_APP=run:app and use the app created at import.
"""
import socket
import sys

# Setup logging before any other app imports
from app.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger()

HOST = "127.0.0.1"
PORT_START = 5000
PORT_RANGE = 20  # try 5000..5019

# Defaults from app.config.Config — must be overridden in production
_DEFAULT_SECRET_KEY = "dev-secret-change-in-production"
_DEFAULT_INVITE_CODE = "chitchat-invite"


def _validate_environment():
    """Fail loudly if SECRET_KEY or INVITE_CODE are still at default values (unless CHITCHAT_ALLOW_DEFAULTS=1)."""
    import os
    if os.environ.get("CHITCHAT_ALLOW_DEFAULTS") == "1":
        return
    from app.config import Config
    if getattr(Config, "SECRET_KEY", None) == _DEFAULT_SECRET_KEY:
        logger.error(
            "SECRET_KEY is still the default. Set CHITCHAT_SECRET_KEY in the environment."
        )
        raise SystemExit(
            "FATAL: CHITCHAT_SECRET_KEY must be set to a non-default value. "
            "Set the CHITCHAT_SECRET_KEY environment variable."
        )
    if getattr(Config, "INVITE_CODE", None) == _DEFAULT_INVITE_CODE:
        logger.error(
            "INVITE_CODE is still the default. Set CHITCHAT_INVITE_CODE in the environment."
        )
        raise SystemExit(
            "FATAL: CHITCHAT_INVITE_CODE must be set to a non-default value. "
            "Set the CHITCHAT_INVITE_CODE environment variable."
        )


def find_available_port(host, start, count=PORT_RANGE):
    """Return the first port in [start, start+count) that is free to bind."""
    for port in range(start, start + count):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return port
        except OSError:
            continue
    return start  # fallback; will likely fail with clear error


# Create app for Flask CLI (flask db upgrade, etc.) and for run below
from app import create_app

app = create_app()


if __name__ == "__main__":
    try:
        logger.info("ChitChat starting")

        with app.app_context():
            _validate_environment()
            # Migrations and seed run automatically in create_app()

        host = HOST
        port = find_available_port(host, PORT_START)
        if port != PORT_START:
            logger.info("Port %s in use; using %s", PORT_START, port)
        logger.info("ChitChat ready")
        print(f"\n  ChitChat running at  http://{host}:{port}  — open in your browser.\n")
        app.socketio.run(app, host=host, port=port, debug=False, use_reloader=False)
    except SystemExit:
        raise
    except Exception:
        logger.exception("ChitChat failed to start")
        sys.exit(1)
