# ChitChat — Architecture

## Overview

ChitChat is a private chat server for up to 10 users. It uses a modular, SOLID-oriented layout with clear separation between foundation, models, socket logic, and UI.

## Directory Layout

```
chitchat/
├── run.bat              # Windows: venv, deps, launch run.py
├── run.py               # Entry point; env validation, migrations + seed, then socketio.run
├── requirements.txt     # Python dependencies (includes flask-migrate)
├── migrations/          # Flask-Migrate (Alembic) — versions/001_initial_schema.py, env.py
├── logs/                # Runtime logs (git-ignored except .gitkeep)
│   ├── app.log          # General activity (start, connections)
│   └── errors.log       # Exceptions with stack traces and local variable context
├── instance/            # App instance data (DB, etc.; created at runtime)
└── app/
    ├── __init__.py      # App factory (create_app)
    ├── config.py        # Configuration (invite code, DB, secret)
    ├── logging_config.py # Logging setup (logs dir, handlers)
    ├── models.py        # (Step 2) Users, Messages, IgnoreList
    ├── templates/
    │   └── chat.html    # (Step 4) Chat UI (Vanilla JS)
    └── ...              # Routes, socket handlers, services as needed
```

## Foundation (Step 1)

- **Environment**: Python 3.11+; `.venv`; `requirements.txt` (Flask, Flask-SocketIO, Flask-Migrate, eventlet, Flask-SQLAlchemy).
- **Windows**: `run.bat` creates/activates `.venv`, installs deps silently, runs `run.py` with minimal console output.
- **Database**: Schema is managed by **Flask-Migrate (Alembic)**. `run.py` runs `flask db upgrade` and then seeds default rooms/users. No ad-hoc `ALTER TABLE` in app code; first migration is `migrations/versions/001_initial_schema.py`. Existing DBs: run `flask db stamp 001_initial` once.
- **Environment safety**: `run.py` validates `CHITCHAT_SECRET_KEY` and `CHITCHAT_INVITE_CODE` are non-default; exits with a clear message if not.
- **Logging**: `/logs` directory; `app.log` for general activity; `errors.log` for exceptions with **full stack traces and local variable context** per frame (Recursive Learning Loop).
- **Docs**: `TECH_STACK.md`, `ARCHITECTURE.md`, `migrations/README`.

## Data Model (Step 2)

- **Users** — Registered only with a valid **Simple Invite Code** (no open sign-up).
- **Messages** — Stored per room; SQLAlchemy + SQLite.
- **Ignore list** — User-to-user; stored in DB; frontend soft-hides ignored users’ messages.

## Real-Time (Step 3)

- **Flask-SocketIO** over **eventlet** for WebSockets.
- Events: join room, send message, **user_typing**, **load_more_messages**; server broadcasts to room.
- On **join room**: server sends last 50 messages (server-side ignore filter), plus **has_more**; client can request older messages via **load_more_messages** (before_id).
- **Typing**: client emits **user_typing** (debounced); server broadcasts to room; client shows “[User] is typing…” and clears after 5s.
- **Link previews**: when a chat message contains a URL, server fetches OG metadata (app/link_preview.py) and attaches **link_previews** to the message payload; client renders a card with minimize.

## UI (Step 4)

- Single chat interface in `app/templates/chat.html` using **Vanilla JS**, Socket.IO client, and **marked.js** for Markdown in messages.
- **Display name** (from /nick) and **status** (from /status) shown in whois; message header shows display name when set.
- **Load older messages** button at top of message list; **typing indicator** above the input; **link preview** cards with minimize per message.

## Design Principles

- **SOLID / DRY**: Single responsibility modules; shared config and logging; app factory for testability.
- **Modular**: Foundation → Models → Socket logic → UI; each step builds on the previous.
- **Deployment-ready**: Config via environment variables; Linux-compatible paths and server choice (eventlet) for VPS.
