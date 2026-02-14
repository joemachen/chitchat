"""
Run database migrations. Use this if migrations fail at startup or you prefer to run them manually.
Usage: .venv\\Scripts\\python.exe migrate.py   (Windows, from project root)
       python migrate.py   (if venv is activated)
"""
import os
os.environ.setdefault("CHITCHAT_ALLOW_DEFAULTS", "1")

from app import create_app

app = create_app()
print("Migrations complete.")
