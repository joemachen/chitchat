"""Application version for deploy announcements and System Events."""
import os

# Set CHITCHAT_VERSION in env (e.g. from CI: git describe --tags) or default
VERSION = os.environ.get("CHITCHAT_VERSION", "2.0.0")
