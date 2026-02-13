# ChitChat — Roadmap

A Discord/mIRC-style chat app for you and your friends (target: **max 10 people** at once). Persistent, local-first for now, with a path to online deployment. Focus: solid foundation, privacy & security, futureproofing, and the best features of this class of app.

---

## Current State (as of this update)

### Stack & foundation

- **Stack**: Flask, Flask-SocketIO, eventlet, Flask-SQLAlchemy, SQLite, Vanilla JS; optional pywebview standalone.
- **Run**: `run.py` (browser), `run_standalone.py` (native window). Port fallback: if 5000 is in use, tries 5001–5019 automatically.
- **Foundation**: Logging (`logs/app.log`, `logs/errors.log`), migrations (rooms, users, messages, topic columns, Super Admin), docs (TECH_STACK, ARCHITECTURE, ROADMAP).

### Auth & users

- **Auth**: Invite-code registration, login, logout, password reset, “remember me” (cookie + server token for standalone).
- **Super Admin**: User “Joe” (and any user) can be Super Admin via migration/Settings. Super Admins only: access Settings, kick users, create/edit/delete channels, assign Super Admin to others. Non–Super Admins cannot perform those actions.

### Rooms & channels

- **Rooms**: general, Stats (stats view, no send form), **Acrophobia** (game bot), plus user-created rooms. Full CRUD for channels (Super Admin only); room order per user (drag-and-drop).
- **Channel topic**: Any user can set with **/topic &lt;content&gt;**. Topic is pinned at top of channel with “Set by &lt;user&gt; on &lt;date/time&gt;”; toast notifies the room when topic is updated.

### Real-time & commands

- **Presence**: Online/offline in user list; connect/disconnect broadcasts.
- **Messages**: Join room → full history; send message; /ping &lt;username&gt;, /em or /me &lt;text&gt; (emote); ignore list; right-click user → View profile, Kick (Super Admin only).
- **IRC-style**: **/whois &lt;username&gt;** — shows account created, online/offline, IP, time connected (modal to requester only). **/topic &lt;content&gt;** for channel topic.

### Acrophobia (AcroBot)

- **AcroBot** in room **Acrophobia**: hosts rounds (acronym → submit phrase → vote → winner). Commands: **/start**, **/vote N**, **/help**, **/msg acrobot help** (full help and rules); **/msg acrobot &lt;anything&gt;** gets a short reply when bot is active.
- **Activate/deactivate**: In Settings (Super Admin only), “AcroBot is online” toggle. When off, bot does not start rounds or accept votes; user list shows AcroBot as offline. When on, AcroBot appears online in user list.
- **Timers**: Submit phase (60s) and vote phase (45s) advance automatically; bot messages persisted and broadcast like normal chat.

### UX

- **Copy/paste**: Message text, channel topic, room names, and stats area are explicitly selectable (user-select: text). Paste in the message input works as usual.
- **Context menu**: Right-click on a username (in messages or user list) shows View profile and Kick (if Super Admin); menu stays open until click outside or an action is chosen.

---

## Principles

- **Solid foundation & architecture**: Clear separation of models, sockets, routes, game logic; app factory; migrations that don’t break startup.
- **Privacy & security**: Invite-only; no open sign-up; hashed passwords; session/remember handling; future: HTTPS, rate limits, optional E2E considerations.
- **Futureproof**: Config-driven (env, config module); DB migrations; modular features (Acrophobia, whois, topic) so new channels/bots are additive.
- **Bulletproof**: Graceful handling of missing DB columns, missing rooms/users; port fallback; logging and error logs; no silent failures where avoidable.
- **User-friendly**: Clear UI, room list, history, pings, emotes, stats, game channel, Settings, whois modal, toasts; responsive feedback.
- **Efficient**: Single DB, in-memory presence and game state where appropriate; history loaded on room join; targeted broadcasts.

---

## Phases

### Phase 1 — Local, stable (mostly done)

- **Done**: AcroBot + Acrophobia room in migration; /help and /msg acrobot help; activate/deactivate in Settings; port fallback; copy/paste; context menu fix; Super Admin + Settings + topic + whois.
- **Optional remaining**:
  - Acrophobia: optional /score (in-memory or DB), optional per-round time limits.
  - UX: unread indicators per room; optional sound on ping/message.
  - Quality: light E2E or integration tests; README mention of /help and commands.

### Phase 2 — Richer chat & moderation

- **Chat**: Optional file/image uploads (size limits, instance/ or configurable storage). Optional reply-to-message (threading or inline). Optional edit/delete own message.
- **Moderation**: Optional room roles (e.g. owner); room-level mute; admin controls (invite codes, room create/delete, user list) — partly covered by Super Admin today.
- **Persistence**: Optional message search (by room, user, text); export room history (JSON/HTML).

### Phase 3 — Online deployment (separate phase)

- **Hosting**: Deploy on VPS or PaaS (single instance + Gunicorn/eventlet); reverse proxy (e.g. Nginx) with HTTPS. Env-based config: SECRET_KEY, DATABASE_URL, INVITE_CODE, ALLOWED_ORIGINS.
- **Security**: HTTPS only; secure cookies; rate limiting (login, register, send_message); optional CAPTCHA on register; optional 2FA.
- **Discovery**: Optional server URL + invite link; optional public room list; keep ~10 concurrent users per instance; document scaling (sticky sessions for WebSockets, etc.).

### Phase 4 — Polish & “best of” features

- **Discord/mIRC-like**: Optional DMs (1:1 rooms); optional server name and branding; optional themes (light/dark); status (online/away/dnd); rich presence (“in Acrophobia”, “in general”).
- **Acrophobia & bots**: Optional persistent Acrophobia scores (DB), leaderboard in Stats or in-room; more bot channels (trivia, word games) using same pattern.
- **Reliability**: Optional reconnection with history re-fetch; “last N messages” cache; optional read receipts or “last seen”.

### Phase 5 — Mobile distribution (long-term, on hold)

- **Status**: On hold until otherwise stated. Final step in the roadmap.
- **Goal**: Prepare for App Store / Play Store distribution (e.g. wrapped web app or native build). Mandatory items for store approval are in place: **Report Message** (database + UI) and **Delete My Account** (Settings).
- **Future**: Packaging, signing, store listing, push notifications (optional), and any platform-specific compliance.

---

## Matrix-inspired / spec-aligned improvements

Ideas from the [Matrix Specification](https://spec.matrix.org/latest/) that fit ChitChat without requiring federation. Implement incrementally; supports futureproofing and optional interoperability.

- **Event model & types**: Extend event types (e.g. `chitchat.room.topic`, `chitchat.game.acrophobia.round_start`). Validate event/message bodies (schema + size) before persisting — treat payloads as untrusted.
- **State vs message events**: Treat topic, membership, ranks as "state events" with a `state_key`; keep messages and emotes as message events. Clear split makes room settings and member power levels easier to add later.
- **Event graph / depth**: Add a depth (or similar) field so "load older" and threading use a single, well-defined order (e.g. strictly greater than parents). Enables consistent ordering and "messages since depth N" style APIs.
- **Private user data**: Key/value store per user for preferences (theme, notification toggles, etc.) without new DB columns per setting. Symmetrical to profile data; stored server-side per account.
- **Namespacing**: Namespace custom event types (e.g. `chitchat.game.acrophobia.*`) so core, AcroBot, and future features don't collide.
- **Room aliases**: Optional human-readable aliases (e.g. `#general`, `#acrophobia`) that resolve to room IDs for shareable links and discovery; internal storage stays room_id–based.
- **User & device identity**: Optional stable string user ID (e.g. `@username:yourdomain.com`) for APIs and future use; optional "devices" (e.g. remember-me sessions) for "logout this device" or a sessions UI later.

*Suggested placement: event model, state vs message, validation, namespacing → Phase 2; private user data, aliases, user/device identity → Phase 4.*

---

## Summary

| Phase | Focus |
|-------|--------|
| **1** | Local stability — **largely done**; optional /score, unread/sounds, tests |
| **2** | Richer chat (files, reply, edit), moderation, search/export |
| **3** | Online: HTTPS, deployment, rate limits, invite links |
| **4** | DMs, themes, persistent scores, more bots, reconnection |
| **5** | **Mobile distribution** — long-term, on hold; Report Message & Delete Account in place for store approval |

See **Matrix-inspired / spec-aligned improvements** for event model, state vs message events, private user data, room aliases, and user/device identity (incremental, no federation required).

The app is built so that **online is a phase**, not a rewrite: the same codebase, with config and deployment choices (env, HTTPS, host), becomes a small, private “Discord/mIRC-like” server for you and your friends (max ~10 users), with a solid base for privacy, security, and future features.
