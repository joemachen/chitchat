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
        with app.app_context():
            from flask_migrate import upgrade
            from app import _seed_default_data, _run_message_retention_cleanup, _post_deploy_announcement

            if os.environ.get("CHITCHAT_SKIP_MIGRATIONS") == "1":
                print("[gunicorn_run] skipping migrations (CHITCHAT_SKIP_MIGRATIONS=1)", flush=True)
            else:
                print("[gunicorn_run] running migrations (45s timeout)...", flush=True)
                try:
                    # Run migrations in subprocess with timeout - avoids blocking/hang killing startup
                    # Don't capture output - let migration stdout/stderr stream to logs
                    mig_script = """
import sys
print('[mig] starting', flush=True)
from run import app
print('[mig] app loaded', flush=True)
from flask_migrate import upgrade
app.app_context().push()
print('[mig] calling upgrade()...', flush=True)
try:
    upgrade()
    print('[gunicorn_run] migrations OK', flush=True)
except BaseException as e:
    import traceback
    print(f'[mig] ERROR: {type(e).__name__}: {e}', flush=True)
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(1)
"""
                    mig_env = dict(os.environ)
                    mig_env["PYTHONUNBUFFERED"] = "1"
                    result = subprocess.run(
                        [sys.executable, "-u", "-c", mig_script],  # -u = unbuffered
                        env=mig_env,
                        timeout=45,
                    )
                    if result.returncode != 0:
                        print(f"[gunicorn_run] MIGRATION FAILED (rc={result.returncode}) - see output above", flush=True)
                except subprocess.TimeoutExpired:
                    print("[gunicorn_run] MIGRATION TIMEOUT (45s) - continuing; run /run-migrations later", flush=True)
                except Exception as mig_err:
                    print(f"[gunicorn_run] MIGRATION FAILED (continuing): {mig_err}", flush=True)
                    traceback.print_exc()
            # Belt-and-suspenders: create any missing tables that Alembic may have
            # recorded as applied but never actually created (e.g. due to a startup crash).
            print("[gunicorn_run] ensuring all tables exist...", flush=True)
            try:
                from app.models import db
                from sqlalchemy import inspect as sa_inspect
                inspector = sa_inspect(db.engine)
                existing = set(inspector.get_table_names())
                from app.models import Poll
                if "polls" not in existing:
                    print("[gunicorn_run] polls table missing — creating directly...", flush=True)
                    Poll.__table__.create(db.engine, checkfirst=True)
                    print("[gunicorn_run] polls table created OK", flush=True)
            except Exception as tbl_err:
                print(f"[gunicorn_run] table ensure failed (non-fatal): {tbl_err}", flush=True)
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
