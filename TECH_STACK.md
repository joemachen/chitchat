# ChitChat — Tech Stack

## Runtime & Language

- **Python 3.11+** — Required for the project; enforced by `run.bat` and recommended for type hints and performance.

## Backend

- **Flask** — Web framework; routes, app factory, and request handling.
- **Flask-SocketIO** — WebSocket support for real-time messaging.
- **Flask-Migrate** — Database migrations (Alembic); replaces ad-hoc schema changes; `flask db upgrade` / `flask db migrate`.
- **gevent** — Async/WSGI server used as the SocketIO async mode; Linux-compatible for VPS deployment.
- **Flask-SQLAlchemy** — ORM; SQLite for development; PostgreSQL (Neon) for production. Schema is managed by Flask-Migrate (Alembic).
- **requests + BeautifulSoup4** — Link preview: fetch first URL in a message and extract Open Graph (og:title, og:description, og:image) for preview cards.

## Data

- **SQLite** — Default database (file-based) for local development.
- **PostgreSQL (Neon)** — Production database; set `DATABASE_URL` or `CHITCHAT_DATABASE_URI` (config normalizes `postgres://` to `postgresql://`).

## Frontend

- **Vue 3 (CDN)** — Composition API, reactive state; single template `chat.html`. No build step.
- **marked.js** — Markdown rendering for message content (bold, italics, code blocks); loaded from CDN.
- **Link previews** — Server fetches Open Graph data (requests + BeautifulSoup); client renders preview cards with minimize.
- **Typing indicators** — WebSocket `user_typing` event; “[User] is typing…” above the input.
- **Message pagination** — Last 50 messages on join; “Load older messages” fetches more; server-side room-mute filter.

## Tooling & Environment

- **Virtual environment** — `.venv` created and used by `run.bat` on Windows.
- **Logging** — Python `logging`; `logs/app.log` (general), `logs/errors.log` (exceptions with full stack traces and **local variable context** per frame for debugging).
- **Environment safety** — `run.py` validates that `CHITCHAT_SECRET_KEY` and `CHITCHAT_INVITE_CODE` are set to non-default values; exits with a clear error if not.

## Deployment

- **Koyeb + Neon**: `Procfile` (`web: python gunicorn_run.py`). Set `DATABASE_URL`, `CHITCHAT_SECRET_KEY`, `CHITCHAT_INVITE_CODE` in Koyeb environment variables. Optional: `CHITCHAT_VERSION` for deploy announcements (posted to System Events only when version changes); `CHITCHAT_SKIP_MIGRATIONS=1` to skip migrations at startup (debug only).
- **Gunicorn** — Production WSGI server; gevent worker for WebSocket support.
- **psycopg2-binary** — PostgreSQL driver for Neon.
