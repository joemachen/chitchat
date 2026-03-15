# ChitChat — Architecture

## Overview

ChitChat is a private chat server for up to 10 users. It uses a modular, SOLID-oriented layout with clear separation between foundation, models, socket logic, and UI.

## Directory Layout

```
chitchat/
├── run.bat              # Windows: venv, deps, launch run.py
├── run.py               # Entry point; env validation, migrations + seed, then socketio.run
├── wsgi.py              # Gunicorn entry point; gevent monkey_patch before imports
├── Procfile             # Koyeb: web: python gunicorn_run.py
├── requirements.txt    # Python dependencies (flask-migrate, gunicorn, psycopg2-binary)
├── migrations/          # Flask-Migrate (Alembic) — versions/001–028, env.py
├── logs/                # Runtime logs (git-ignored except .gitkeep)
│   ├── app.log          # General activity (start, connections)
│   └── errors.log       # Exceptions with stack traces and local variable context
├── instance/            # App instance data (DB, etc.; created at runtime)
├── .github/workflows/   # GitHub Actions (build-standalone on tag push)
└── app/
    ├── __init__.py      # App factory (create_app)
    ├── config.py        # Configuration (invite code, DB, secret)
    ├── logging_config.py # Logging setup (logs dir, handlers)
    ├── models.py        # (Step 2) Users, Messages, RoomMute; IgnoreList (legacy)
    ├── templates/
    │   └── chat.html    # (Step 4) Chat UI (Vue 3)
    └── ...              # Routes, socket handlers, services as needed
```

## Foundation (Step 1)

- **Environment**: Python 3.11+; `.venv`; `requirements.txt` (Flask, Flask-SocketIO, Flask-Migrate, gevent, gunicorn, psycopg2-binary, Flask-SQLAlchemy).
- **Windows**: `run.bat` creates/activates `.venv`, installs deps silently, runs `run.py` with minimal console output.
- **Database**: Schema is managed by **Flask-Migrate (Alembic)**. `create_app()` runs `flask db upgrade` and seeds default rooms/users. SQLite by default; **PostgreSQL** (Neon) supported via `DATABASE_URL` or `CHITCHAT_DATABASE_URI`. Config normalizes `postgres://` to `postgresql://`.
- **Environment safety**: `run.py` validates `CHITCHAT_SECRET_KEY` and `CHITCHAT_INVITE_CODE` are non-default; exits with a clear message if not.
- **Logging**: `/logs` directory; `app.log` for general activity; `errors.log` for exceptions with **full stack traces and local variable context** per frame (Recursive Learning Loop).
- **Docs**: `TECH_STACK.md`, `ARCHITECTURE.md`, `TECHNICAL_OVERVIEW.md`, `UI_GUIDELINES.md`, `ROADMAP.md`, `migrations/README`.
- **Production**: `Procfile` for Koyeb; gunicorn with gevent worker. Role permissions (Super Admin configures rookie/bro/fam) in `role_permissions` table.
- **Standalone builds**: GitHub Actions workflow (`.github/workflows/build-standalone.yml`) builds Windows, macOS, and Linux executables on tag push (`v*`); uploads to GitHub Releases. Standalone window checks GitHub releases API on startup and shows a dismissible update banner when a newer version exists; Settings → General includes a Version section (standalone only) with current version and update status. Title bar shows version (e.g. `No Homers Club v3.5.32`); header shows app name and username only. Login page has "Get the app" button linking to releases.

## Data Model (Step 2)

- **Users** — Registered only with a valid **Simple Invite Code** (no open sign-up).
- **Messages** — Stored per room; SQLAlchemy + SQLite. `message_type` can be `’chat’`, `’emote’`, or `’poll’`.
- **Polls** — `polls` table (migration 028). Timed polls created via `!poll`; one active poll per room; votes stored as JSON; auto-closes via gevent timer.
- **Room mute** — Per-room mute; frontend hides muted users’ messages.

## Real-Time (Step 3)

- **Flask-SocketIO** over **gevent** for WebSockets.
- Events: join room, send message, **user_typing**, **load_more_messages**; server broadcasts to room.
- On **join room**: server sends last 50 messages (server-side room-mute filter), plus **has_more**; client can request older messages via **load_more_messages** (before_id).
- **Typing**: client emits **user_typing** (debounced); server broadcasts to room; client shows “[User] is typing…” and clears after 5s.
- **Link previews**: when a chat message contains a URL, server fetches OG metadata (app/link_preview.py) and attaches **link_previews** to the message payload; client renders a card with minimize.

## UI (Step 4)

- Single chat interface in `app/templates/chat.html` using **Vue 3** (CDN, Composition API), Socket.IO client, and **marked.js** for Markdown in messages.
- **UI guidelines** (`UI_GUIDELINES.md`): Custom confirm/alert/prompt modals; edit modals with responsive dimensions; design tokens for dark/light themes.
- **Display name** (from /nick) and **status** (from /status) shown in whois; message header shows display name when set. **Letter avatars** — circular avatars with user initial and colored background (customizable in Settings → Profile).
- **Load older messages** button at top of message list; **typing indicator** above the input; **link preview** cards with minimize per message.
- **Spoilers** — Wrap text or image URLs in `||double pipes||`; frosted-glass overlay until click to reveal; **Reveal all spoilers** button when room has spoilers.
- **Version display** — Title bar and header show app version; standalone users see Version section in Settings → General with update check and Download link.

## Design Principles

- **SOLID / DRY**: Single responsibility modules; shared config and logging; app factory for testability.
- **Modular**: Foundation → Models → Socket logic → UI; each step builds on the previous.
- **Deployment-ready**: Config via environment variables; Linux-compatible paths; Koyeb + Neon Postgres supported; gunicorn + gevent for production.
