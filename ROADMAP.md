# ChitChat — Roadmap

A Discord/mIRC-style chat app for you and your friends (max ~10 people). Persistent, local-first, with Koyeb + Neon for online deployment. Flask, SocketIO, gevent, SQLite/Postgres, Vue 3.

**Current state (v3.5.37):** Rooms, DMs, presence, Acrophobia (AcroBot), Prof Frink trivia, Homer quotes, System Events, server-level roles, message cache, private user data, room aliases. Login page server status. Discord-style bot isolation in user list. Role permissions HTTP save; mobile + New room; MP4 inline playback. Message edit on mobile (long-press, tap-to-show Edit/Reply). Giphy lightbox fix. WebSocket attempted by default in production. Standalone window opens Koyeb app (no local server); session persists between restarts; in-app update check (GitHub API, dismissible banner); Settings → General Version section (standalone) with update status and Download link; title bar shows version (header shows app name and username only). PyInstaller or GitHub Actions (Windows + macOS + Linux → Release). Homer welcome DM on first login; monthly random quote DM if away 30+ days. Login page: Get the app button (releases). 30+ new Homer quotes. Themes, typing indicators, link previews, inline reply, edit/delete, reactions, search, export, audit log. **Spoilers** — `||text||` or `||image URL||`; frosted overlay; click to reveal; Reveal all spoilers button. **/help** — Categorized (Chat & Presence, Navigation & Settings, Fun & Media, Admin & Roles). **Polls** — `!poll "Question?" A, B, C [--duration N]`; timed polls with live vote counts and progress bars; auto-closes after duration; one active poll per room; results announced on close. External links open in system browser (standalone). **Settings** — Users — Roles layout right-aligned to match Rooms section.

---

## Principles

- **Solid foundation** — Clear separation of models, sockets, routes; migrations; no silent failures.
- **Privacy & security** — Invite-only; hashed passwords; rate limits.
- **User-friendly** — Clear UI, toasts, context menus, responsive feedback.
- **Efficient** — In-memory presence and cache where appropriate; targeted broadcasts.

---

## Next

1. **Export UI polish** — Expand export flow if needed.
2. **Acro history** — Last N acronyms per channel to reduce repeats (optional).

---

## Backlog

- **Voice/audio chat** — Discord-style voice channels.
- Other minigames (Trivia done).
- Matrix-inspired: event model, state vs message, depth, validation — pick incrementally.
- Phase 5: Mobile distribution — on hold.

---

## Suggested additions (gaps to consider)

### Security

- **2FA/MFA** — Two-factor auth for account protection.
- **Session management** — "Logout all devices", view active sessions, revoke tokens.
- **Account lockout** — Temporary lock after N failed logins.
- **Password policy** — Min length, complexity (optional).

### Usability

- **Message delivery/retry** — Indicate failed sends; retry without resending.
- **Offline indicator** — Clear "disconnected" state; queue messages for retry.
- **Paste images** — Paste from clipboard into message input.
- **Drag-and-drop upload** — Drag files onto message area.
- **Loading skeletons** — Placeholder UI while history loads.

### Futureproofing

- **API versioning** — Versioned REST or socket events for mobile clients.
- **Webhooks** — Outbound webhooks for integrations (e.g. Slack, Zapier).
- **OAuth/SSO** — Optional "Sign in with Google" etc.
- **Automated DB backup** — Scheduled backups for Neon/Postgres.
