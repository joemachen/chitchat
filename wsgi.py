"""
WSGI entry point for gunicorn. gevent.monkey.patch_all() before any other imports.
"""
import gevent.monkey
gevent.monkey.patch_all()

from run import app
