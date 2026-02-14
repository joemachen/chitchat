"""
WSGI entry point for gunicorn. Runs eventlet.monkey_patch() before any other imports
so that RLock and other stdlib objects are properly greened.
"""
import eventlet
eventlet.monkey_patch()

from run import app
