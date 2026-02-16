# ChitChat — Technical Overview

This document is a detailed technical overview of the ChitChat codebase for reviewers (e.g., AI assistants) who may suggest improvements, refactors, or new features. It describes architecture, stack, data model, real-time layer, security, and known constraints.

---

## 1. Purpose and scope

**ChitChat** is a **private, small-scale chat application** (target: up to ~10 concurrent users) in the spirit of Discord/mIRC. It is:

- **Invite-only**: No open sign-up; registration requires a preconfigured invite code.
- **Local-first by default**: Runs on `127.0.0.1` with SQLite; same codebase deploys online (Koyeb + Neon Postgres).
- **Feature set**: Multi-room chat with history, DMs (1:1 rooms), presence (online/away/dnd/invisible), slash commands, channel topics, edit profile (status, away message, bio, avatar color; announces in System Events; auto-replies to DMs when away), letter avatars (Discord-style initials with customizable background), an in-channel stats view, system events (join/leave/online/offline; deploy announcements with release notes only when version changes), an Acrophobia minigame bot, a Homer bot (!Simpsons for random quotes), a Prof Frink trivia bot (#Trivia: !trivia, !trivia X for 1–7 rounds, !daily, !set-difficulty, !set-seasons; hot streaks; DM replies), message edit/delete, file/image uploads, link previews (OG metadata; GIF URLs render inline without duplicate preview cards), custom confirm/alert/prompt modals (no native dialogs), and admin moderation with role permissions (kick, channel CRUD, assign Super Admin, reset stats).

**Explicitly out of scope for now**: Sound/notifications. File/image uploads are supported (instance/uploads/; ephemeral on redeploy).

---

## 2. Technology stack

| Layer | Technology | Version / notes |
|-------|------------|-----------------|
| **Language** | Python | 3.11+ recommended (type hints, run scripts) |
| **Web framework** | Flask | 3.x (`requirements.txt`: `flask>=3.0.0`) |
| **Real-time** | Flask-SocketIO | 5.3+; WebSockets over eventlet |
| **Async/WSGI** | eventlet | 0.40+; used as SocketIO async mode and for Acrophobia timers |
| **ORM / DB** | Flask-SQLAlchemy | 3.1+; SQLite (dev) / PostgreSQL/Neon (prod) |
| **Auth** | Session + cookie | Flask session; optional “remember me” with signed cookie (itsdangerous, via Flask) and disk fallback for standalone window |
| **Frontend** | Vue 3 (CDN) | Composition API, reactive state; single template `chat.html` |
| **Socket client** | Socket.IO (client) | 4.7.2 (CDN in template) |
| **Standalone UI** | pywebview | 4.4+; optional native window wrapper |

**Config**: `app/config.py` — `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, `INVITE_CODE`, `PERMANENT_SESSION_LIFETIME`, etc. Environment variables: `CHITCHAT_SECRET_KEY`, `CHITCHAT_DATABASE_URI` or `DATABASE_URL`, `CHITCHAT_INVITE_CODE`. Config normalizes `postgres://` to `postgresql://`.

**Entry points**:

- **Browser**: `run.py` — sets up logging, finds an available port (5000–5019), runs `app.socketio.run(app, host="127.0.0.1", port=port, debug=False, use_reloader=False)`.
- **Production (Koyeb)**: `wsgi.py`; `Procfile`: `python gunicorn_run.py` (runs eventlet monkey_patch before gunicorn).
- **Standalone window**: `run_standalone.py` — loads the same app URL in a pywebview window; remember-me token can be stored on disk when cookies are unreliable.

---

## 3. Architecture and layout

### 3.1 Directory structure

```
chitchat/
├── run.py                 # Entry point (logging, port fallback, socketio.run)
├── wsgi.py                # Gunicorn entry; eventlet.monkey_patch before imports
├── Procfile               # Koyeb: python gunicorn_run.py
├── run_standalone.py      # Optional: pywebview wrapper
├── run.bat / run-standalone.bat
├── requirements.txt
├── migrations/            # Flask-Migrate (Alembic) versions 001–019
├── instance/              # Created at runtime; SQLite DB and remember token
├── logs/                  # app.log, errors.log (logging_config)
├── app/
│   ├── __init__.py        # App factory, DB init, migrations, SocketIO init, route/socket registration
│   ├── config.py          # Config class (SECRET_KEY, DB, INVITE_CODE, session)
│   ├── logging_config.py  # File handlers for app.log and errors.log; no console by default
│   ├── models.py          # User, Room, Message, AcroScore, AppSetting, IgnoreList, MessageReaction, UserRoomRead, UserRoomNotificationMute, MessageReport, AuditLog, RolePermission, RoomMute
│   ├── auth.py            # Invite validation, register, login, remember token, password reset
│   ├── routes.py          # HTTP: /, /login, /register, /reset-password, /logout, /chat
│   ├── sockets.py         # All SocketIO handlers and presence/stats helpers
│   ├── acrophobia.py      # Acrophobia game logic (in-memory state, bot replies)
│   ├── homer.py           # Homer bot (!Simpsons trigger, random quotes, online/offline toggle)
│   ├── version.py         # VERSION from CHITCHAT_VERSION env (deploy announcements)
│   ├── templates/         # login, register, reset_password, chat.html
│   └── static/            # auth.css, etc.
├── ARCHITECTURE.md        # High-level architecture
├── TECH_STACK.md          # Stack summary
├── TECHNICAL_OVERVIEW.md  # This file
├── UI_GUIDELINES.md       # Modal, alert, and form UI standards (see §3.3)
├── ROADMAP.md             # Phases and feature list
└── IDEAS.md               # Plus-up / backlog ideas
```

### 3.2 Application factory and startup

- **`create_app()`** in `app/__init__.py`:
  1. Creates Flask app, loads `app.config.Config`.
  2. Ensures `instance` path exists.
  3. Inits Flask-SQLAlchemy, runs **Flask-Migrate `upgrade()`** (Alembic migrations 001–019), then **`_seed_default_data(app)`**, then **`_post_deploy_announcement(app)`** (posts deploy announcement to System Events only when version changes).
  4. Registers HTTP routes via `register_routes(app)`.
  5. Creates SocketIO app (`async_mode="eventlet"`, loggers disabled).
  6. Registers socket handlers via `register_socket_handlers(socketio)`.
  7. Attaches `app.socketio` and returns the app.

- **Migrations**: Flask-Migrate (Alembic); schema changes are applied with raw SQL `ALTER TABLE` and existence checks (e.g. `topic`, `topic_set_by_id`, `topic_set_at`, `dm_with_id` on `rooms`; `room_order_ids`, `is_super_admin`, `away_message`, `avatar_bg_color` on `users`; `room_id`, `message_type` on `messages`). Versions 001–020. Ensures default rooms and bots exist: **general**, **Stats**, **Acrophobia**, **System Events**, **Trivia**; users **AcroBot**, **System**, **Homer**, and **Prof Frink**; and optionally promotes user “Joe” to Super Admin.

### 3.3 Design principles

- **UI guidelines**: See `UI_GUIDELINES.md` for modal, alert, and form standards. The app uses custom confirm/alert/prompt modals (never native `alert`/`confirm`/`prompt`); edit modals follow responsive dimensions for desktop and mobile.
- **Separation of concerns**: Models, auth, routes, sockets, and game logic are in distinct modules; Acrophobia returns “bot replies” that the socket layer persists and emits.
- **Single source of truth**: Messages and room state in SQLite; presence and Acrophobia game state in process memory.
- **No console logging by default**: All logging goes to `logs/app.log` and `logs/errors.log` (see `logging_config.py`).

---

## 4. Data model

All entities are in `app/models.py` (Flask-SQLAlchemy, SQLite).

### 4.1 User

- **Table**: `users`.
- **Fields**: `id`, `username` (unique), `password_hash`, `created_at`, `room_order_ids` (JSON array of room ids as text), `is_super_admin`, `rank`, `away_message`, `display_name`, `status_line`, `bio`, `avatar_bg_color` (hex for letter avatar), `user_status`, `last_seen`, `message_retention_days`.
- **Relations**: `messages`, `created_rooms` (Room.created_by_id). Legacy: `ignoring` / `ignored_by` (IgnoreList) kept for cascade delete only.
- **Notes**: No open sign-up; invite code checked in `auth.py`. Passwords hashed with Werkzeug. AcroBot and System are special users created by migration.

### 4.2 Room

- **Table**: `rooms`.
- **Fields**: `id`, `name`, `created_at`, `created_by_id`, `topic`, `topic_set_by_id`, `topic_set_at`, `dm_with_id`, `is_protected`.
- **DM semantics**: If `dm_with_id` is set, the room is a DM between `created_by_id` and `dm_with_id`. Name is stored as `"DM"`; display name (“DM: <other_username>”) is derived on the client from `created_by_id`, `created_by_username`, `dm_with_username`, and current user id.
- **Relations**: `created_by`, `topic_set_by`, `dm_with`, `messages` (cascade delete).
- **Protected rooms**: **general** cannot be deleted. **Stats**, **Acrophobia**, **System Events**, **Trivia** can only be deleted from Settings by an admin (backend checks `from_settings` on delete).

### 4.3 Message

- **Table**: `messages`.
- **Fields**: `id`, `room_id`, `user_id`, `content`, `created_at`, `message_type` (`'chat'` or `'emote'`), `parent_id`, `edited_at`, `attachment_url`, `attachment_filename`, `link_previews` (JSON), plus legacy `room` (string) for backward compatibility.
- **Relations**: `user`, `room`, `parent` (reply), `reactions` (MessageReaction).
- **Notes**: All channel history is stored here; Stats view is computed from this table (no separate stats storage). Deleting “Stats data” means deleting all rows in `messages`.

### 4.4 AppSetting

- **Table**: `app_settings`.
- **Fields**: `key` (unique), `value` (text).
- **Usage**: Key-value store for app-wide settings. `default_room_id` — Admin chooses which channel users see on login when no room is specified.

### 4.5 IgnoreList (legacy)

- **Table**: `ignore_list`.
- **Status**: Ignore functionality removed. Table retained for cascade delete when users are deleted. No UI or socket handlers use it.

---

## 5. Authentication and session

- **Login**: POST `/login` with username/password; session stores `user_id` and `username`; optional “remember me” sets a signed cookie (`chitchat_remember`) and optionally a token file in `instance/` for standalone.
- **Before request**: `routes.py`’s `before_request` restores session from remember-me cookie or from disk if cookie is missing (e.g. standalone window).
- **Socket.IO**: No separate socket auth; the client connects after loading the chat page (which requires an active session). Session is used in each socket handler via `session.get("user_id")`; connection is rejected if not authenticated (`on_connect` returns `False`).
- **Password reset**: `/reset-password` with username, invite code, and new password (invite code required).
- **Security**: `SECRET_KEY` and `INVITE_CODE` should be set via environment in production; default values are for development only.

---

## 6. Real-time layer (Socket.IO)

**Transport**: Flask-SocketIO with **eventlet** (single process, cooperative multitasking). Rooms are named `room_{room_id}` (integer room id).

### 6.1 Presence

- **In-memory**: `_online_user_ids`, `_sid_to_user_id`, `_sid_to_connected_at`, `_sid_to_remote_addr` in `sockets.py`.
- **Connect**: On `connect`, user is added to these structures and a system event “{username} came online” is posted to the **System Events** room; `user_list_updated` is broadcast.
- **Disconnect**: On `disconnect`, user is removed and “{username} went offline” is posted to System Events; `user_list_updated` is broadcast again.
- **AcroBot**: Treated as “online” when the Settings toggle is on (`is_acrobot_active()`), independent of socket presence.
- **System (service)**: A service account that posts system events (e.g. "came online", "went offline", nick changes) to the System Events room. It has no socket connection and is always offline. The UI hides it from the user list. It cannot be removed without breaking system event posting.

### 6.2 Socket events (server-side)

| Event (client → server) | Handler | Auth | Description |
|-------------------------|--------|------|-------------|
| `connect` | `on_connect` | Session | Reject if no `user_id`; else track presence and post system event. |
| `disconnect` | `on_disconnect` | — | Remove from presence; post “went offline”. |
| `get_rooms` | `on_get_rooms` | Yes | Emit `rooms_list` with rooms in user’s order. |
| `join_room` | `on_join_room` | Yes | Join socket room; emit `room_joined` with history (or stats for Stats room), room_muted_in_room, users, rooms. |
| `send_message` | `on_send_message` | Yes | Slash-command handling and/or persist message; broadcast `new_message`. |
| `create_room` | `on_create_room` | Super Admin or create_room | Create room; broadcast `rooms_updated`; emit `room_created` and optionally switch. |
| `update_room` | `on_update_room` | Super Admin or update_room | Rename room; emit `topic_updated`-style update. Protected channels: only Super Admin can rename. |
| `delete_room` | `on_delete_room` | Super Admin or delete_room | Block for general and protected channels unless `from_settings`; delete room; broadcast. |
| `save_room_order` | `on_save_room_order` | Yes | Persist `room_order_ids` for user; emit `rooms_list`. |
| `get_user_profile` | `on_get_user_profile` | Yes | Emit `user_profile` with user dict. |
| `get_or_create_dm` | `on_get_or_create_dm` | Yes | Find or create DM room between current user and `other_user_id`; emit `dm_room`; if created, broadcast `rooms_updated`. |
| `kick_user` | `on_kick_user` | Super Admin or kick_user | Emit `kicked_from_room` to target’s socket(s). AcroBot and Homer: Super Admin only. |
| `set_super_admin` | `on_set_super_admin` | Super Admin only | Set/unset `is_super_admin`; broadcast `user_list_updated`. |
| `get_acrobot_status` | `on_get_acrobot_status` | Any | Emit `acrobot_status` (active flag). |
| `set_acrobot_active` | `on_set_acrobot_active` | Super Admin or acrobot_control | Turn AcroBot on/off; broadcast `acrobot_status` and `user_list_updated`. |
| `reset_stats_data` | `on_reset_stats_data` | Super Admin or reset_stats | Require `confirm: "RESET"`; delete all Message rows; emit `stats_reset` to requester. |
| `get_role_permissions` | `on_get_role_permissions` | Super Admin only | Emit `role_permissions` for Settings UI (includes `default_room_id`). |
| `set_role_permission` | `on_set_role_permission` | Super Admin only | Update role permission; broadcast `role_permissions`. |
| `set_default_room` | `on_set_default_room` | Super Admin only | Set default channel for login; persist in `app_settings`; broadcast `role_permissions`. |
| `edit_message` | `on_edit_message` | Yes | Edit own message; emit `message_edited` to room. |
| `delete_message` | `on_delete_message` | Yes | Delete own message; emit `message_deleted` to room. |
| `add_reaction` / `remove_reaction` | `on_add_reaction` / `on_remove_reaction` | Yes | Toggle emoji reaction; broadcast `reaction_updated`. |
| `delete_my_messages` | `on_delete_my_messages` | Yes | Bulk delete own messages (confirm required); emit `messages_deleted`, `my_messages_deleted`. |
| `set_message_retention` | `on_set_message_retention` | Yes | Set auto-delete days (7/30/90 or None); emit `message_retention_updated`. |
| `delete_user` | `on_delete_user` | Super Admin only | Delete user and cascade; broadcast `user_list_updated`, `rooms_updated`. |

### 6.3 Send message and slash commands

**Order of handling** in `on_send_message` (after validation):

1. **`/help`** — Post a single message (from the user) listing all ChitChat and Acrophobia commands; persist and emit.
2. **`/away [message]`** — Set or clear `user.away_message`; post emote “is away: …” or “is no longer away”; persist and emit.
3. **`/whois <username>`** — Look up user (case-insensitive); emit `whois_result` to requester only (includes online, IP, connected_at for Super Admin).
4. **`/topic <text>`** — Set `room.topic`, topic_set_by_id, topic_set_at; emit `topic_updated` to room.
5. **Acrophobia room** — If room name is “Acrophobia”, call `acrophobia.handle_message`; if consumed, persist and emit bot messages; if round started, schedule submit-phase timer.
6. **`/ping <username>`** — Emit `user_pinged` to room (username case-insensitive); if target has `away_message`, emit `away_message` to sender only.
7. **`/em <text>` / `/me <text>`** — Treat as emote; persist as `message_type='emote'` and emit.
8. **Otherwise** — Persist as normal chat message and emit `new_message`.

All persisted messages (including help and emotes) are stored in `messages` and broadcast to `room_{room_id}`.

### 6.4 Acrophobia integration

- **Module**: `app/acrophobia.py`. State is **in-memory**: `_games` (per room: phase, acronym, submissions, votes, end_time, rounds_remaining), `_acrobot_active` (toggle from Settings). **Scores** are persisted in `acro_scores` (AcroScore model).
- **Phases**: `idle` → `submitting` (60 s) → `voting` (45 s) → `idle`. Submit and vote timers are scheduled with **eventlet.spawn_after** in `sockets.py`. **Submit phase**: warnings at 30s and 15s remaining; **vote phase**: countdown from 15s down to 1s (urgency when ≤15s). Callbacks call `advance_submit_phase` / `advance_vote_phase`, then persist and emit bot messages via `_acrophobia_emit_bot_messages`.
- **Acronyms**: Random **4- or 5-letter** uppercase string (`random.choices(string.ascii_uppercase, k=4 or 5)`), not a fixed list.
- **Commands**: `/start` or `/start X` (X=1–7 consecutive rounds), `/vote N`, `/score`, `/help`, `/msg acrobot help` (and variants). User submissions during submit phase are not stored as messages; only bot messages are persisted. **DM voting**: Users can vote via DM with AcroBot; AcroBot acknowledges vote receipt (e.g. "Thanks. I got your vote for this round, L'il Bro."). AcroBot often addresses users as "L'il Bro" or "L'il Homey".

### 6.5 Stats

- **Stats room**: When a user joins the room named “Stats”, server emits `room_joined` with `history: []` and `stats: _get_stats()`.
- **`_get_stats()`**: Aggregates from **Message** table: top 10 typers (message count per user), active hours (messages per hour 0–23), favorite words (top 5 users by message count, top 10 words each, stop words excluded). Also includes **Acrophobia leaderboard** (AcroScore) and **Trivia leaderboard** (TriviaScore). No separate stats table; “reset Stats data” deletes all messages.

### 6.6 System events

- **System Events room**: Receives messages from user “System” for “{username} came online” and “{username} went offline” (on connect/disconnect); "{username} is away: {message}" and "{username} is no longer away" when away message is set/cleared via Edit profile or /away. **Deploy announcement**: On app startup (after migrations and seed), `_post_deploy_announcement(app)` posts "Server redeployed (v{VERSION})" to System Events only when the version has changed (not on every redeploy). Version comes from `app/version.py` (env `CHITCHAT_VERSION`, default `2.8.3`). Implemented via `_post_system_event(content)` in `sockets.py` and direct Message creation in `app/__init__.py`.

---

## 7. Frontend (chat UI)

- **Single file**: `app/templates/chat.html` — HTML, CSS, and JavaScript in one template. Rendered by Flask with `user` (current user); no separate JS bundle.
- **Socket client**: Socket.IO 4.7.2 from CDN; connection with `withCredentials: true`. No explicit reconnection logic documented; Socket.IO client has built-in reconnect.
- **Main structure**: Header (title, Settings, Log out), status line, main area: **room list** (left), **chat area** (center: channel topic, messages div, send form), **user list** (right). **Letter avatars**: Each message and user list item shows a circular avatar with the user's initial and a colored background (customizable in Settings → Profile → Avatar color; deterministic when not set). Bots show "(bot)" suffix. Scrollbars themed for dark/light mode. DMs appear in the same room list as “DM: <other_username>”; no separate DM drawer. **Mobile (<768px)**: 3-tab bottom nav (Rooms, DMs, Settings) replaces hamburger; when viewing a room, DM, or Settings, the nav hides for full-screen content; back arrow opens home panel (profile: nick, status, time connected, stats preview); Rooms/DMs open the room list drawer; Settings opens Settings view; inline presence bar ("X online") above input opens bottom sheet with Online/Offline users (tap or swipe handle to dismiss); fixed bottom bar with safe-area padding when nav visible; chat area padding adjusts when nav hidden.
- **State**: `currentUserId`, `currentRoom`, `allRooms`, `allUsersWithStatus`, `showingSettings`, `acrobotActive`, `roomOrderIds`, etc. Room list is reordered by drag-and-drop; order persisted via `save_room_order`.
- **Global features** (apply to all rooms, DMs, and Acrophobia): **@mention highlights** (message pulse, room badge), **tab flashing** (document.title alternates when mentioned and tab is hidden), **link previews** (OG metadata for URLs in messages; minimize per preview). These are not Acrophobia-specific.
- **Key behaviors**:
  - **join_room** on load (no explicit room_id → server uses default channel from Settings; Admin configures this in Settings → Default channel).
  - **room_joined**: Renders room list, user list, and either message history or stats view; applies room-mute filter (messages from muted users get class `hidden`).
  - **new_message**: Appends to messages div; scrolls to bottom; ignores if message room ≠ current room.
  - **Protected channels**: Stats, Acrophobia, System Events (and general) have no delete button in room list; delete only via Settings (admin) with `from_settings: true`. Only Super Admin can rename protected channels. Non-admin users editing a protected channel see an alert instead of the name input but can still edit the topic.
  - **DM styling**: When `currentRoom.is_dm`, messages container has class `is-dm` (different background/border/color).
  - **Context menu**: Right-click (or long-press on mobile) on username (in messages or user list) → **Edit profile** (self only: status, away message), Whois, Message (opens/creates DM), Kick (Super Admin or kick_user permission; AcroBot/Homer: Super Admin only). Right-click on channel → Edit channel (name and topic). **Reply**: Click reply on a message to pre-fill the input with quoted text (`> @DisplayName:\n> [content]\n\n`). **Username lookup**: /whois, /ping, /msg, and @mentions use case-insensitive matching (e.g. /whois joe finds "Joe").
  - **Settings**: Rendered in place of chat when “Settings” is open: **Profile** tab (nick, status, visibility, away message, bio, avatar color), **Appearance** tab (Theme Dark/Light, high-contrast; chat background color; font picker for system fonts), **Notifications** tab (room notification mute), **Chat history** (delete all own messages, auto-delete retention 7/30/90 days), AcroBot toggle, Homer toggle, Prof Frink toggle, Stats reset (prompt to type RESET), Channels (with delete for non-general), **Bot channels** (admin: which channels each bot can respond in), Role Permissions table (Super Admin only), Super Admin checkboxes, **Default channel** dropdown (Super Admin only). Reset stats emits `reset_stats_data` with `confirm: "RESET"`; on `stats_reset`, toast and optional re-join Stats room to refresh view.
- **Toasts**: Ping and away messages shown as temporary toasts (e.g. ping-toast class, auto-remove after a few seconds).

---

## 8. Security and permissions

- **Authentication**: All socket handlers that need a user check `session.get("user_id")`; unauthenticated connect is rejected.
- **Super Admin** (top role, `rank='super_admin'`): Checked via `_is_super_admin(user_id)` (User.is_super_admin). Full access; only Super Admin can assign Super Admin (`set_super_admin`) and configure role permissions. Other actions use `_has_permission()`: Super Admin always allowed; else checks `role_permissions` table (create_room, update_room, delete_room, kick_user, set_user_rank, acrobot_control, homer_control, reset_stats, export_all).
- **Room membership**: No per-room membership table; any authenticated user can join any room and send messages. Kick only notifies the target client (`kicked_from_room`) and does not remove from DB “membership” (there is none).
- **Input**: Slash commands are parsed server-side; message content is stored as-is (no rich HTML from client). Frontend escapes/links content (e.g. linkify) when rendering.
- **CORS**: `cors_allowed_origins=[]` (same-origin only by default).
- **Secrets**: SECRET_KEY and INVITE_CODE should be overridden in production; no secrets in repo.

---

## 9. Known limitations and constraints

- **Single process**: eventlet single-threaded; no horizontal scaling without changing design (e.g. Redis adapter for SocketIO, shared presence).
- **Message edit/delete**: Supported for own messages via styled modal (textarea, Shift+Enter for new lines); bulk delete on reset stats.
- **File/image uploads**: Supported (instance/uploads/); configurable size limit.
- **Acrophobia state**: Game state (phase, submissions, votes) is in-memory and lost on restart; scores are persisted in `acro_scores`.
- **Migrations**: Flask-Migrate (Alembic); versioned migrations in `migrations/versions/`.
- **Stats reset**: Deleting all messages is irreversible and affects all channels.
- **Phase 3 (online deployment)**: Done (Koyeb + Neon Postgres). **Sound** remains optional.

**Koyeb WebSocket troubleshooting**: If users see "Connecting..." and never connect, the app uses ProxyFix for reverse-proxy headers. If WebSocket upgrade fails (e.g. HTTP/2 on Koyeb), set `CHITCHAT_SOCKET_POLLING_ONLY=1` in Koyeb environment to force HTTP long-polling. Ensure the service runs a single instance (`-w 1` in Procfile) or add Redis for multi-instance Socket.IO.

---

## 10. File-by-file summary (for quick reference)

| File | Role |
|------|------|
| `run.py` | Logging setup, port 5000–5019 fallback, `create_app()`, `socketio.run()`. |
| `gunicorn_run.py` | Koyeb launcher; runs eventlet.monkey_patch before gunicorn to fix RLock warning. |
| `wsgi.py` | Gunicorn entry; imports app from run. |
| `app/__init__.py` | App factory, DB init, Flask-Migrate upgrade, seed, deploy announcement, SocketIO init, register routes and sockets. |
| `app/config.py` | SECRET_KEY, DB URI, INVITE_CODE, session/remember duration. |
| `app/version.py` | VERSION from CHITCHAT_VERSION env (default 2.8.3); used for deploy announcements. |
| `app/logging_config.py` | File handlers for app.log and errors.log; get_logger(). |
| `app/models.py` | User, Room, Message, AcroScore, AppSetting, IgnoreList (legacy), MessageReaction, UserRoomRead, UserRoomNotificationMute, MessageReport, AuditLog, RolePermission, RoomMute; to_dict() where needed. |
| `app/auth.py` | Invite validation, register_user, get_user_by_credentials, remember token (create/load/save to disk), reset_password. |
| `app/routes.py` | Index, login, register, reset-password, logout, chat; before_request (restore session from remember); context_processor (inject user). |
| `app/sockets.py` | Presence globals, _get_stats, _get_users_with_online_status, _rooms_sorted_for_user (channels + DMs filtered/deduplicated per user), _user_by_username (case-insensitive lookup), Acrophobia timer scheduling, _post_system_event, all @socketio.on handlers. |
| `app/acrophobia.py` | _random_acronym, _game, handle_message (help, start, /start X, vote, score, submissions, DM voting, L'il Bro/Homey nicknames), advance_submit_phase, advance_vote_phase, AcroScore (persisted), in-memory _games. |
| `app/homer.py` | Homer bot: is_homer_active, set_homer_active, get_random_simpsons_quote, get_homer_dm_reply; !Simpsons trigger in any room; DM replies. |
| `app/templates/chat.html` | Full chat UI (Vue 3): room list, messages, user list, context menu, Settings view, socket listeners, modals (profile, whois, edit message/room, search, room switcher Ctrl+K). |

---

## 11. Suggested review focus (for AI or human reviewers)

When suggesting changes or features, consider:

1. **Consistency**: Preserve existing patterns (e.g. emit payloads as dicts with clear keys; Super Admin / permission checks via `_has_permission`).
2. **Security**: Any new endpoint or socket event should enforce auth and, if applicable, Super Admin or the relevant permission.
3. **Persistence**: Acrophobia game state is in-memory; scores are persisted (AcroScore). Any “persistent scores” or new game state would need a migration and model.
4. **Frontend**: Single template with Vue 3 (CDN); no build step. Larger UI changes may warrant splitting CSS/JS or introducing a minimal build.
5. **Migrations**: Flask-Migrate (Alembic); add new migrations for schema changes.
6. **Testing**: No tests in the repo yet; suggestions for E2E or integration tests (e.g. login, send message, join room, Acrophobia round) would be valuable.
7. **Docs**: ROADMAP.md, IDEAS.md, and this TECHNICAL_OVERVIEW.md should be updated if behavior or scope changes.

This overview should give Gemini (or any reviewer) enough context to propose concrete, consistent improvements or features.
