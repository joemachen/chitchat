"""
WSGI entry point for gunicorn. gevent.monkey_patch() before any other imports.
"""
import gevent.monkey
gevent.monkey.patch_all()

from run import app
