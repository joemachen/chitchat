"""
Gunicorn launcher: run gevent.monkey.patch_all() before any other imports.
Runs migrations and seed BEFORE starting gunicorn so the app responds to health checks quickly.
"""
import gevent.monkey
gevent.monkey.patch_all()

import os
import sys
import traceback
from gunicorn.app.wsgiapp import run

if __name__ == "__main__":
    # Clear GUNICORN_CMD_ARGS so Koyeb/env cannot override our wsgi:app or worker class
    os.environ.pop("GUNICORN_CMD_ARGS", None)

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
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    # Use explicit args only - do NOT append sys.argv[1:] (Koyeb may pass main:app etc)
    sys.argv = [sys.argv[0], "--worker-class", "gevent", "-w", "1", "wsgi:app"]
    sys.exit(run())
