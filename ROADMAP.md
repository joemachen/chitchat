# ChitChat — Roadmap

A Discord/mIRC-style chat app for you and your friends (target: **max 10 people** at once). Persistent, local-first for now, with a path to online deployment. Focus: solid foundation, privacy & security, futureproofing, and the best features of this class of app.

---

## Current State (v3.5.0)

### Stack & foundation

- **Stack**: Flask, Flask-SocketIO, gevent, Flask-SQLAlchemy, SQLite (dev) / PostgreSQL/Neon (prod), Vue 3 (CDN); optional pywebview standalone.
- **Run**: `run.py` (browser), `run_standalone.py` (native window). Port fallback: if 5000 is in use, tries 5001–5019 automatically.
- **Production**: Koyeb + Neon Postgres; `Procfile` + `wsgi.py`; gunicorn with gevent worker.
- **Foundation**: Logging (`logs/app.log`, `logs/errors.log`), migrations (Alembic, 001–022), docs (TECH_STACK, ARCHITECTURE, TECHNICAL_OVERVIEW, UI_GUIDELINES, ROADMAP).

### Auth & users

- **Auth**: Invite-code registration, login, logout, password reset, "remember me" (cookie + server token for standalone).
- **Super Admin** (top role): Full access; configures role permissions for Rookie, Bro, Fam. Super Admin only: access Settings, assign Super Admin to others.
- **Role permissions**: Super Admin can grant/revoke per-role permissions (create_room, update_room, delete_room, kick_user, set_user_rank, acrobot_control, homer_control, frink_control, reset_stats, export_all). Bro/Fam with permissions can perform those actions without being Super Admin.

### Rooms & channels

- **Rooms**: general, Stats (stats view: top typers, active hours, favorite words, Acrophobia & Trivia leaderboards), **Acrophobia** (game bot), **Trivia** (Prof Frink bot), plus user-created rooms. Full CRUD for rooms (Super Admin or create_room/update_room/delete_room permission); room order per user (drag-and-drop on desktop; Move up/down in context menu on mobile). **Protected rooms**: Only Super Admin can rename protected rooms; others see an alert when editing but can still edit the topic. **Default room**: Super Admin can set which room users see on login (Settings → Default room).
- **Channel topic**: Any user can set with **/topic &lt;content&gt;**. Topic is pinned at top of channel with "Set by &lt;user&gt; on &lt;date/time&gt;"; toast notifies the room when topic is updated.

### Real-time & commands

- **Presence**: Online/offline in user list; connect/disconnect broadcasts.
- **Messages**: Join room → full history; send message; **inline reply** (parent_id, quoted content, jump to original); edit/delete own message; /ping &lt;username&gt;, /em or /me &lt;text&gt; (emote); room mute; right-click user → Whois, Kick (Super Admin or kick_user permission; AcroBot/Homer: Super Admin only).
- **Typing indicators**: "User is typing…" above input (user_typing event; 5s timeout).
- **IRC-style**: **/whois &lt;username&gt;** — shows account created, online/offline, IP, time connected (modal to requester only). **/topic &lt;content&gt;** for channel topic. **Username lookup**: /whois, /ping, /msg, and @mentions are case-insensitive (e.g. /whois joe finds "Joe").

### Acrophobia (AcroBot)

- **AcroBot** in room **Acrophobia**: hosts rounds (acronym → submit phrase → vote → winner). Commands: **/start** or **/start X** (X=1–7 consecutive rounds), **/vote N**, **/score** (leaderboard), **/help**, **/msg acrobot help** (full help and rules); **/msg acrobot &lt;anything&gt;** gets a short reply when bot is active. **DM voting**: Users can vote via DM with AcroBot; AcroBot acknowledges vote receipt.
- **Activate/deactivate**: In Settings (Super Admin only), "AcroBot is online" toggle.
- **Timers**: Submit phase (60s) with warnings at 30s and 15s remaining; vote phase (45s) with countdown from 10s to 1s. **Timer display** above input: "Submit: Xs" / "Vote: Xs" (and Trivia: "Answer: Xs"). Persistent scores in DB; leaderboard in-room and in Stats.

### UX

- **Global features** (all rooms, DMs, Acrophobia): @mention highlights (message pulse, room badge), tab flashing when mentioned and tab is hidden, link previews (OG metadata for URLs; minimize per preview; GIF URLs render inline playing with click-to-pause for Giphy/Tenor). Muted rooms show 🔇 emoji. Custom confirm/alert/prompt modals for destructive actions.
- **Copy/paste**: Message text, channel topic, room names, and stats area are explicitly selectable (user-select: text). Paste in the message input works as usual. **Multi-line input**: Shift+Enter for new line; Enter to send. Edit message uses a styled modal with full message visibility.
- **Context menu**: Right-click on a username (in messages or user list) shows Whois and Kick. Right-click your own name to set status (Online, Away, Do Not Disturb, Invisible). Right-click (or long-press on mobile) a room for Move up/down, Mute notifications, Edit room, Unmute users (if muted).
- **Mobile**: Content view hides 3-tab nav for full-screen chat; back arrow opens channel list (Rooms + DMs) with 3-tab nav. Profile (nick, status, away message, bio, avatar color) in Settings → Profile. Log out: Settings tab or footer of channel list.
- **DMs**: Consolidated per user pair (deduplicated); only DMs you participate in are shown.
- **Homer**: Type **!Simpsons** in any room to trigger a random Simpsons quote (when Homer is online). Online/offline toggle in Settings.
- **Prof Frink**: Trivia room; !trivia, !trivia X (1–7 rounds, 45s per question), !score, !set-difficulty, !set-seasons; bot channel configurable in Settings.

---

## Principles

- **Solid foundation & architecture**: Clear separation of models, sockets, routes, game logic; app factory; migrations that don't break startup.
- **Privacy & security**: Invite-only; no open sign-up; hashed passwords; session/remember handling; future: HTTPS, rate limits, optional E2E considerations.
- **Futureproof**: Config-driven (env, config module); DB migrations; modular features (Acrophobia, whois, topic) so new channels/bots are additive.
- **Bulletproof**: Graceful handling of missing DB columns, missing rooms/users; port fallback; logging and error logs; no silent failures where avoidable.
- **User-friendly**: Clear UI, room list, history, pings, emotes, stats, game channel, Settings, whois modal, toasts; responsive feedback.
- **Efficient**: Single DB, in-memory presence and game state where appropriate; history loaded on room join; targeted broadcasts.

---

## Phases

### Phase 1 — Local, stable ✅ done

- AcroBot + Acrophobia room; /help and /msg acrobot help; activate/deactivate in Settings; port fallback; copy/paste; context menu; Super Admin + Settings + topic + whois; role permissions; message reactions; unread indicators (server-backed); inline replies; typing indicators; Acrophobia /score and timer display.

### Phase 2 — Richer chat & moderation

- **Chat**: File/image uploads done; inline reply done; edit/delete own message done.
- **Moderation**: Optional **room roles** (e.g. owner); room-level mute done; admin controls partly covered by Super Admin and role permissions.
- **Persistence**: Message search done; export room history (JSON/HTML) — routes exist for export.

### Phase 3 — Online deployment ✅ done

- **Hosting**: Koyeb + Neon Postgres; `Procfile` + `wsgi.py`; gunicorn with gevent worker. Env: `DATABASE_URL`, `CHITCHAT_SECRET_KEY`, `CHITCHAT_INVITE_CODE`.
- **Security**: HTTPS via Koyeb; secure cookies; rate limiting done; CAPTCHA remains optional.
- **Discovery**: Optional server URL + invite link; optional public room list; keep ~10 concurrent users per instance.

### Phase 4 — Polish & "best of" features

- **Discord/mIRC-like**: DMs done; themes (light/dark/high-contrast) done; status (online/away/dnd/invisible) done.
- **Acrophobia & bots**: Persistent scores done; leaderboard done; Prof Frink trivia done; bot channel management done.
- **Reliability**: Reconnection with history re-fetch done. **"Last N messages" cache** — implemented (in-memory, 100 per room).

### Phase 5 — Mobile distribution (long-term, on hold)

- **Status**: On hold until otherwise stated.
- **Goal**: Prepare for App Store / Play Store distribution. Mandatory items for store approval in place: Report Message, Delete My Account.
- **Future**: Packaging, signing, store listing, push notifications (optional), platform-specific compliance.

---

## Room roles ✅ implemented (v3.5.0)

- **Room owner** — Creator; can assign moderators, set topic, kick from room, delete room (unless protected).
- **Room moderator** — Can kick users from that room; can edit room (e.g. topic).
- **Member** — Default; can read/send.
- **Room ban** — Banned user cannot send messages in that room.
- **Socket events:** `kick_from_room`, `set_room_moderator`, `user_kicked_from_room`, `room_moderators_updated`.

---

## "Last N messages" cache ✅ implemented (v3.5.0)

- In-memory cache of last 100 messages per room.
- Join/reconnect uses cache when available; otherwise fetches from DB and populates cache.
- Cache updated on new message, edit, delete, wipe.

---

## Matrix-inspired / spec-aligned improvements

Ideas from the [Matrix Specification](https://spec.matrix.org/latest/) that fit ChitChat without requiring federation. Implement incrementally.

### Items

- **Event model & types**: Extend event types (e.g. `chitchat.room.topic`, `chitchat.game.acrophobia.round_start`). Validate event/message bodies (schema + size) before persisting.
- **State vs message events**: Treat topic, membership, ranks as "state events" with a `state_key`; keep messages and emotes as message events.
- **Event graph / depth**: Add a depth field for "load older" with well-defined order; enables "messages since depth N" style APIs.
- **Private user data**: Key/value store per user for preferences (theme, notification toggles, etc.) without new DB columns per setting.
- **Namespacing**: Namespace custom event types (e.g. `chitchat.game.acrophobia.*`).
- **Room aliases**: Human-readable aliases (e.g. `#general`, `#acrophobia`) that resolve to room IDs for shareable links.
- **User & device identity**: Optional stable string user ID (e.g. `@username:yourdomain.com`); optional "devices" for "logout this device" or sessions UI.

### Benefits

- **Futureproofing**: Cleaner data model; easier to add features (room power levels, room settings) without ad-hoc columns.
- **Interoperability**: If you ever want Matrix bridge or export, the structure is closer to spec.
- **Private user data**: Add preferences (theme, mute settings) without schema migrations per setting.
- **Room aliases**: Shareable links like `chitchat.example.com/#general`.
- **Validation**: Schema + size checks reduce malformed or oversized payloads.

### Drawbacks

- **Effort**: Significant refactor of message/event flow; not trivial.
- **Complexity**: More concepts (state vs message, depth, namespacing) for a small app.
- **YAGNI**: For max 10 users, current model may be sufficient; Matrix patterns are built for scale/federation.
- **Migration**: Existing messages would need depth/type mapping; one-time migration work.

**Suggested placement:** Event model, state vs message, validation, namespacing → Phase 2; private user data, aliases, user/device identity → Phase 4. Pick incrementally; no need to do all at once.

---

## Plus-up / backlog (from former IDEAS.md)

Items not yet done; pick and choose.

- **Sound** — Optional ping sound when mentioned or DM'd (excluded per your request).
- **Acro history** — Last N acronyms in this channel so repeats are less likely (optional).
- **Other minigames** — Word chain or a second bot (Trivia done).
- **Room roles** — See above.
- **"Last N messages" cache** — See above.
- **Export room history** — Routes exist; UI/flow could be expanded.

### Already in place (for reference)

- Message reactions, edit/delete, unread indicators, theme, keyboard shortcuts, typing indicators, search, file uploads, inline reply, Acrophobia /score and timer, audit log, rate limits, health endpoint.
- @mention highlights, link previews, /help, Stats reset, Homer, DMs.

---

## Summary

| Phase | Focus |
|-------|--------|
| **1** | Local stability — **done** |
| **2** | Richer chat, moderation, search/export — most done; room roles optional |
| **3** | Online: Koyeb + Neon — **done** |
| **4** | Polish — most done; "Last N" cache and Matrix-inspired items optional |
| **5** | Mobile distribution — on hold |

---

## Next up (prioritized)

1. **Health endpoint** — *(done)*
2. **Keyboard shortcuts** — *(done)*
3. **Message reactions** — *(done)*
4. **Unread indicators** — *(done)*
5. **Search** — *(done)*
6. **Reconnection + history re-fetch** — *(done)*
7. **Netsplit** — *(done)*
8. **Accessibility** — *(done)*
9. **Rate limits** — *(done)*
10. **Audit log** — *(done)*

**Remaining optional:** Acro history, export UI polish, Phase 5 (mobile). Room roles, cache, private data, aliases, validation done in v3.5.0.

---

The app is built so that **online is a phase**, not a rewrite: the same codebase, with config and deployment choices (env, HTTPS, host), becomes a small, private "Discord/mIRC-like" server for you and your friends (max ~10 users), with a solid base for privacy, security, and future features.
