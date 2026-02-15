"""
Gunicorn launcher: run eventlet.monkey_patch() before any other imports to fix
"RLock(s) were not greened" warning. Must be the first code that runs in the worker.
"""
import eventlet
eventlet.monkey_patch()

import sys
from gunicorn.app.wsgiapp import run

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "--worker-class", "eventlet", "-w", "1", "wsgi:app"] + sys.argv[1:]
    sys.exit(run())
