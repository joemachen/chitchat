"""
Gunicorn launcher: run eventlet.monkey_patch() before any other imports.
Runs migrations and seed BEFORE starting gunicorn so the app responds to health checks quickly.
"""
import eventlet
eventlet.monkey_patch()

import os
import sys
from gunicorn.app.wsgiapp import run

if __name__ == "__main__":
    # Run maintenance before web starts so app is ready for health checks immediately
    os.environ["CHITCHAT_MAINTENANCE_DONE"] = "1"
    try:
        from run import app
        with app.app_context():
            from flask_migrate import upgrade
            from app import _seed_default_data, _run_message_retention_cleanup, _post_deploy_announcement
            upgrade()
            _seed_default_data(app)
            _run_message_retention_cleanup(app)
            _post_deploy_announcement(app)
    except Exception as e:
        print(f"FATAL: maintenance failed: {e}", file=sys.stderr)
        sys.exit(1)

    sys.argv = [sys.argv[0], "--worker-class", "eventlet", "-w", "1", "--preload", "wsgi:app"] + sys.argv[1:]
    sys.exit(run())
