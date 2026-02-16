"""
Gunicorn launcher: run gevent.monkey.patch_all() before any other imports.
Runs migrations and seed BEFORE starting gunicorn so the app responds to health checks quickly.
"""
import sys
print("[gunicorn_run] starting", flush=True)

import os
import gevent.monkey
gevent.monkey.patch_all()

import subprocess
import traceback

if __name__ == "__main__":
    # Clear GUNICORN_CMD_ARGS so Koyeb/env cannot override our wsgi:app or worker class
    os.environ.pop("GUNICORN_CMD_ARGS", None)

    # Run maintenance before web starts so app is ready for health checks immediately
    os.environ["CHITCHAT_MAINTENANCE_DONE"] = "1"
    try:
        print("[gunicorn_run] running maintenance...", flush=True)
        print("[gunicorn_run] importing app...", flush=True)
        from run import app
        print("[gunicorn_run] running migrations...", flush=True)
        with app.app_context():
            from flask_migrate import upgrade
            from app import _seed_default_data, _run_message_retention_cleanup, _post_deploy_announcement
            upgrade()
            print("[gunicorn_run] seeding...", flush=True)
            _seed_default_data(app)
            _run_message_retention_cleanup(app)
            _post_deploy_announcement(app)
        print("[gunicorn_run] maintenance done, starting gunicorn...", flush=True)
    except Exception as e:
        # Print to both stdout and stderr so it shows in Koyeb logs
        msg = f"FATAL: maintenance failed: {e}"
        print(msg, flush=True)
        print(msg, file=sys.stderr, flush=True)
        traceback.print_exc()
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.stdout.flush()
        sys.exit(1)

    # Run gunicorn via subprocess with explicit args - no argv/env can override
    port = os.environ.get("PORT", "8000")
    cmd = [
        sys.executable, "-m", "gunicorn",
        "--worker-class", "gevent",
        "-w", "1",
        "--bind", f"0.0.0.0:{port}",
        "wsgi:app",
    ]
    sys.exit(subprocess.run(cmd, env=dict(os.environ)).returncode)
