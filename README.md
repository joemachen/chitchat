# ChitChat

A Discord/mIRC-style chat app for you and your friends (max ~10 people). Persistent, local-first: run it on your machine and open it in a browser or in a standalone window. Invite-only sign-up, rooms, real-time messages, and an Acrophobia game bot.

## Run

- **Windows (browser):** `run.bat` — creates/activates `.venv`, installs deps, runs the server. Open http://127.0.0.1:5000 (or the next free port 5001–5019 if 5000 is in use).
- **Windows (standalone window):** `run-standalone.bat` — same server in a background thread, opens the app in a native window (requires `pywebview`).
- **Manual:** `python run.py` or `python run_standalone.py` from the project root (with `.venv` activated).

## Commands

### In any channel

| Command | Description |
|--------|-------------|
| **/topic** &lt;text&gt; | Set the channel topic (pinned at top; shows who set it and when). |
| **/whois** &lt;username&gt; | IRC-style whois: account created, online/offline, IP, time connected (modal to you only). |
| **/ping** &lt;username&gt; | Notify that user (they see a “pinged you!” toast). |
| **/em** &lt;text&gt; or **/me** &lt;text&gt; | Send an emote: “* username text” in italics. |

### In the Acrophobia channel

Type **/help** or **/msg acrobot help** in that room for full instructions and rules. Summary:

| Command | Description |
|--------|-------------|
| **/help** or **/msg acrobot help** | Full help: how to play, rules, all commands. |
| **/msg acrobot** &lt;anything&gt; | Short reply from the bot (e.g. “AcroBot here. Type /help…”). |
| **/start** | Start a new round (acronym → submit phrase → vote → winner). |
| **/vote** &lt;N&gt; | During voting, vote for submission N (e.g. /vote 1). |
| **/score** | Show the in-channel leaderboard (wins). Scores are in-memory and reset on server restart. |

Super Admins can turn the Acrophobia bot on/off in **Settings** (“AcroBot is online” toggle).

## Docs

- **ARCHITECTURE.md** — Layout, data model, real-time, UI.
- **TECH_STACK.md** — Python, Flask, SocketIO, SQLite/Postgres, Koyeb.
- **TECHNICAL_OVERVIEW.md** — Detailed technical reference for reviewers.
- **ROADMAP.md** — Current state, principles, and phases (local → online → polish).

## Requirements

- Python 3.11+
- See `requirements.txt` (Flask, Flask-SocketIO, eventlet, Flask-SQLAlchemy, etc.). Optional: `pywebview` for the standalone window.
