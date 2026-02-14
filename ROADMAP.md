# ChitChat — Roadmap

A Discord/mIRC-style chat app for you and your friends (target: **max 10 people** at once). Persistent, local-first for now, with a path to online deployment. Focus: solid foundation, privacy & security, futureproofing, and the best features of this class of app.

---

## Current State (as of this update)

### Stack & foundation

- **Stack**: Flask, Flask-SocketIO, eventlet, Flask-SQLAlchemy, SQLite (dev) / PostgreSQL/Neon (prod), Vanilla JS; optional pywebview standalone.
- **Run**: `run.py` (browser), `run_standalone.py` (native window). Port fallback: if 5000 is in use, tries 5001–5019 automatically.
- **Production**: Koyeb + Neon Postgres; `Procfile` + `wsgi.py`; gunicorn with eventlet worker.
- **Foundation**: Logging (`logs/app.log`, `logs/errors.log`), migrations (Alembic, 001–015), docs (TECH_STACK, ARCHITECTURE, TECHNICAL_OVERVIEW, ROADMAP).

### Auth & users

- **Auth**: Invite-code registration, login, logout, password reset, “remember me” (cookie + server token for standalone).
- **Surfer Girl** (top role, formerly “Super Admin”): Full access; configures role permissions for Rookie, Bro, Fam. Surfer Girl only: access Settings, assign Surfer Girl to others.
- **Role permissions**: Surfer Girl can grant/revoke per-role permissions (create_room, update_room, delete_room, kick_user, set_user_rank, acrobot_control, homer_control, reset_stats, export_all). Bro/Fam with permissions can perform those actions without being Surfer Girl.

### Rooms & channels

- **Rooms**: general, Stats (stats view, no send form), **Acrophobia** (game bot), plus user-created rooms. Full CRUD for channels (Surfer Girl or create_room/update_room/delete_room permission); room order per user (drag-and-drop). **Default channel**: Surfer Girl can set which channel users see on login (Settings → Default channel).
- **Channel topic**: Any user can set with **/topic &lt;content&gt;**. Topic is pinned at top of channel with “Set by &lt;user&gt; on &lt;date/time&gt;”; toast notifies the room when topic is updated.

### Real-time & commands

- **Presence**: Online/offline in user list; connect/disconnect broadcasts.
- **Messages**: Join room → full history; send message; edit/delete own message; /ping &lt;username&gt;, /em or /me &lt;text&gt; (emote); room mute; right-click user → View profile, Kick (Surfer Girl or kick_user permission).
- **IRC-style**: **/whois &lt;username&gt;** — shows account created, online/offline, IP, time connected (modal to requester only). **/topic &lt;content&gt;** for channel topic. **Username lookup**: /whois, /ping, /msg, and @mentions are case-insensitive (e.g. /whois joe finds "Joe").

### Acrophobia (AcroBot)

- **AcroBot** in room **Acrophobia**: hosts rounds (acronym → submit phrase → vote → winner). Commands: **/start** or **/start X** (X=1–7 consecutive rounds), **/vote N**, **/help**, **/msg acrobot help** (full help and rules); **/msg acrobot &lt;anything&gt;** gets a short reply when bot is active. **DM voting**: Users can vote via DM with AcroBot; AcroBot acknowledges vote receipt (e.g. “Thanks. I got your vote for this round, L'il Bro”). AcroBot often addresses users as “L'il Bro” or “L'il Homey”.
- **Activate/deactivate**: In Settings (Surfer Girl only), “AcroBot is online” toggle. When off, bot does not start rounds or accept votes; user list shows AcroBot as offline. When on, AcroBot appears online in user list.
- **Timers**: Submit phase (60s) with warnings at 30s and 15s remaining; vote phase (45s) with countdown from 15s to 1s (urgency styling when ≤15s); bot messages persisted and broadcast like normal chat.

### UX

- **Global features** (all rooms, DMs, Acrophobia): @mention highlights (message pulse, room badge), tab flashing when mentioned and tab is hidden, link previews (OG metadata for URLs; minimize per preview). These apply app-wide, not just in Acrophobia.
- **Copy/paste**: Message text, channel topic, room names, and stats area are explicitly selectable (user-select: text). Paste in the message input works as usual. **Multi-line input**: Shift+Enter for new line; Enter to send. Edit message uses a styled modal with full message visibility.
- **Context menu**: Right-click on a username (in messages or user list) shows View profile and Kick (if Surfer Girl or kick_user permission). Right-click your own name to set status (Online, Away, Do Not Disturb, Invisible).
- **Mobile**: Single compact header (hamburger, logo, channel name, info chevron, users); collapsible info drawer for topic/connection; search in hamburger menu; fixed header; chat fills space.
- **DMs**: Consolidated per user pair (deduplicated); only DMs you participate in are shown.
- **Homer**: System user; type **!Simpsons** in any room to trigger a random Simpsons quote (when Homer is online). Online/offline toggle in Settings (Surfer Girl only); homer_control permission. Homer’s status: “It says no HomerS. We're allowed to have one.”

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

- **Done**: AcroBot + Acrophobia room in migration; /help and /msg acrobot help; activate/deactivate in Settings; port fallback; copy/paste; context menu fix; Surfer Girl + Settings + topic + whois; role permissions; **message reactions**; **unread indicators** (server-backed).
- **Optional remaining**:
  - Acrophobia: optional /score (in-memory or DB), optional per-round time limits.
  - UX: unread indicators per room.
  - Quality: light E2E or integration tests; README mention of /help and commands.

### Phase 2 — Richer chat & moderation

- **Chat**: Optional file/image uploads (size limits, instance/ or configurable storage). Optional reply-to-message (threading or inline). Optional edit/delete own message.
- **Moderation**: Optional room roles (e.g. owner); room-level mute; admin controls (invite codes, room create/delete, user list) — partly covered by Surfer Girl and role permissions today.
- **Persistence**: Optional message search (by room, user, text); export room history (JSON/HTML).

### Phase 3 — Online deployment ✅ done

- **Hosting**: Koyeb + Neon Postgres; `Procfile` + `wsgi.py`; gunicorn with eventlet worker. Env: `DATABASE_URL`, `CHITCHAT_SECRET_KEY`, `CHITCHAT_INVITE_CODE`.
- **Security**: HTTPS via Koyeb; secure cookies; rate limiting and CAPTCHA remain optional.
- **Discovery**: Optional server URL + invite link; optional public room list; keep ~10 concurrent users per instance.

### Phase 4 — Polish & “best of” features

- **Discord/mIRC-like**: DMs (1:1 rooms) done; optional server name and branding; themes (light/dark) done; **status (online/away/dnd/invisible)** done — right-click own name; rich presence (“in Acrophobia”, “in general”).
- **Acrophobia & bots**: **Persistent Acrophobia scores (DB)** done; leaderboard in-room; more bot channels (trivia, word games) using same pattern.
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
| **1** | Local stability — **done**; optional /score, unread, tests |
| **2** | Richer chat (files, reply, edit), moderation, search/export — **edit/delete, search done** |
| **3** | Online: Koyeb + Neon — **done** |
| **4** | DMs done, themes done, persistent scores done, reactions done, unread done, mobile layout done; more bots, reconnection |

---

## Next up (prioritized)

1. **Health endpoint** — `GET /health` for uptime checks *(done)*
2. **Keyboard shortcuts** — Ctrl+K room switcher, Esc close modals
3. **Message reactions** — *(done)*
4. **Unread indicators** — *(done)*
5. **Search** — Search messages in current room or all rooms *(done — in-room search; mobile: in hamburger)*
6. **Reconnection + history re-fetch** — Refetch recent messages on reconnect
7. **Netsplit** — Easter egg: `/netsplit` or random fake netsplit for lols
8. **Accessibility** — Semantic HTML, keyboard nav, reduced motion, high-contrast
9. **Rate limits** — Throttle messages per user per minute *(done)*
10. **Audit log** — Surfer Girl view of who did what *(done)*
11. **Voice chat** — 1:1 or small-group (2–4) via WebRTC P2P; long-term
12. **Desktop/screen sharing** — 1:1 or small-group; long-term
| **5** | **Mobile distribution** — long-term, on hold; Report Message & Delete Account in place for store approval |

See **Matrix-inspired / spec-aligned improvements** for event model, state vs message events, private user data, room aliases, and user/device identity (incremental, no federation required).

The app is built so that **online is a phase**, not a rewrite: the same codebase, with config and deployment choices (env, HTTPS, host), becomes a small, private “Discord/mIRC-like” server for you and your friends (max ~10 users), with a solid base for privacy, security, and future features.
