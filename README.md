# ChitChat

A Discord/mIRC-style chat app for you and your friends (max ~10 people). Persistent, local-first: run it on your machine and open it in a browser or in a standalone window. Invite-only sign-up, rooms, real-time messages, an Acrophobia game bot, a Homer bot (!Simpsons), and a Prof Frink trivia bot (#Trivia).

## Run

- **Windows (browser):** `run.bat` — creates/activates `.venv`, installs deps, runs the server. Open http://127.0.0.1:5000 (or the next free port 5001–5019 if 5000 is in use).
- **Windows (standalone window):** `run-standalone.bat` — same server in a background thread, opens the app in a native window (requires `pywebview`).
- **Manual:** `python run.py` or `python run_standalone.py` from the project root (with `.venv` activated).

## Commands

### In any channel

| Command | Description |
|--------|-------------|
| **/help** | Show all commands (slash commands, !Simpsons, context menus, shortcuts). |
| **/topic** &lt;text&gt; | Set the channel topic (pinned at top; shows who set it and when). |
| **/whois** &lt;username&gt; | IRC-style whois: account created, online/offline, IP, time connected, bio (modal to you only). Username case-insensitive. |
| **/nick** &lt;name&gt; | Set your display name (shown in messages and whois). |
| **/status** &lt;text&gt; or **/status** | Set or clear your status line (shown in whois). |
| **/away** &lt;message&gt; or **/away** | Set or clear away message (auto-replies to DMs). |
| **/slap** &lt;nick&gt; | Post action: "* you slaps nick around a bit with a large trout". Invalid/self: Homer mocks. |
| **/ping** &lt;username&gt; | Notify that user (they see a “pinged you!” toast). Username case-insensitive. |
| **!Simpsons** | Homer replies with a random Simpsons quote (when Homer is online). |
| **/em** &lt;text&gt; or **/me** &lt;text&gt; | Send an emote: “* username text” in italics. |

**Context menus** — Right-click (or long-press on mobile) your name to **Edit profile** (status, away message). Right-click a channel to **Edit channel** (name and topic). Right-click other users for Whois, Message, Mute, etc. Menus stay within the viewport on desktop and mobile.

**Shortcuts** — **Ctrl+K** opens the room switcher; **Esc** closes modals.

**Appearance** — Settings → Appearance: theme (dark/light/high-contrast), chat background color, and font (system default or common system fonts).

**Mobile** — On screens under 768px, a 3-tab bottom bar (Rooms, DMs, Settings) replaces the hamburger menu. When viewing a room, DM, or Settings, the nav hides for full-screen content; tap the back arrow (←) to see the full channel list (Rooms + DMs) with the 3-tab nav. Profile (nick, status, away message, bio) is in Settings → Profile.

### In the Acrophobia channel

Type **/help** or **/msg acrobot help** in that room for full instructions and rules. Summary:

| Command | Description |
|--------|-------------|
| **/help** or **/msg acrobot help** | Full help: how to play, rules, all commands. |
| **/msg acrobot** &lt;anything&gt; | Short reply from the bot (e.g. “AcroBot here. Type /help…”). |
| **/start** or **/start X** (X=1–7) | Start a new round or X consecutive rounds (acronym → submit phrase → vote → winner). |
| **/vote** &lt;N&gt; | During voting, vote for submission N (e.g. /vote 1). |
| **/score** | Show the in-channel leaderboard (wins). Scores are persisted in the database. |

### In the Trivia channel

| Command | Description |
|--------|-------------|
| **!trivia** or **!trivia X** (X=1–7) | Get one or X consecutive Simpsons trivia questions. First correct answer wins a point. |
| **!daily** | (admin/frink_control) Toggle automated daily question at 9:00 UTC. |
| **!set-difficulty** [level] | Set difficulty: beginner, intermediate, advanced, master. |
| **!set-seasons** [1-20] | Restrict questions to specific seasons. |
| **!score** or **/score** | Show Trivia leaderboard. |

Admins (or acrobot_control permission) can turn the Acrophobia bot on/off in **Settings** (“AcroBot is online” toggle). Admins (or homer_control permission) can turn Homer on/off ("Homer is online" toggle). Admins (or frink_control permission) can turn Prof Frink on/off ("Prof Frink is online" toggle). **Bot channels** — admins can configure which channels each bot can respond in (Settings → Bot channels).

## Docs

- **ARCHITECTURE.md** — Layout, data model, real-time, UI.
- **TECH_STACK.md** — Python, Flask, SocketIO, SQLite/Postgres, Koyeb.
- **TECHNICAL_OVERVIEW.md** — Detailed technical reference for reviewers.
- **ROADMAP.md** — Current state, principles, and phases (local → online → polish).

## Requirements

- Python 3.11+
- See `requirements.txt` (Flask, Flask-SocketIO, eventlet, Flask-SQLAlchemy, etc.). Optional: `pywebview` for the standalone window.
