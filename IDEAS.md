# ChitChat — Plus-up ideas

Quick list of features and polish that could make the app even better. Pick and choose.

---

## Polish & UX

- **Message reactions** — One-tap emoji reactions on messages (e.g. 👍 😂).
- **Edit / delete own message** — Small “edit” / “delete” on your messages with short time window (e.g. 5 min).
- **Unread indicators** — Badge or bold room name when there are new messages since last view; optional “mark as read”.
- **Sound** — Optional ping sound when mentioned or DM’d (excluded for now per your request).
- **Theme** — Light/dark toggle or accent color in Settings. *(done)*
- **Keyboard shortcuts** — e.g. Ctrl+K to focus search/room switcher, Esc to close modals.

---

## Social & presence

- **Typing indicators** — “User is typing…” in the current channel or DM.
- **Read receipts** — “Seen” or “read at” for DMs (optional, privacy-sensitive).
- **Status** — Beyond away: “busy”, “do not disturb”, custom status line.
- **Rich presence** — “In Acrophobia”, “In general”, “In DM with X” (for future desktop/embed).

---

## Channels & content

- **Pinned messages** — Pin 1–3 messages per channel; show at top or in a “Pinned” strip.
- **Threads** — Reply to a message in a thread; thread summary under the message.
- **Search** — Search messages in current room or all rooms (backend: filter Message by content/room/user).
- **File uploads / images** — **On hold** (no online hosting/storage yet; keeping costs low). When you’re ready, options: (1) **Local-only** — store files under `instance/` or configurable path (no extra cost; not shared across devices). (2) **Free/low-cost tiers** — e.g. Cloudflare R2 (free egress, pay per GB stored), Backblaze B2, or Supabase Storage free tier; single bucket + size limits keeps cost predictable. (3) **Inline tiny images** — base64 in DB or small files on disk for avatars/emotes only.

---

## Acrophobia & games

- **Acro history** — Last N acronyms in this channel so repeats are less likely (optional).
- **Timer display** — Countdown in UI for submit/vote phase (e.g. “45s left”).
- **Other minigames** — Trivia, word chain, or a second bot in another channel.

---

## Moderation & admin

- **Audit log** — Super Admin view: who created/deleted rooms, kicked users, reset stats (store in DB or log file).
- **Rate limits** — Throttle messages per user per minute to avoid spam.
- **Mute** — Mute a user in a channel for X minutes (vs full kick).

---

## Dev & ops

- **Health endpoint** — e.g. `GET /health` for uptime checks when you deploy.
- **Backup** — One-click “Export DB” or “Backup messages” from Settings (Super Admin).
- **Tests** — A few E2E or integration tests for login, send message, Acro round.

---

## Already in place (for reference)

- **Link previews** — OG image + title/description for URLs in messages; minimize per preview.
- **/help** — Lists all slash commands in channel.
- **Stats reset** — Super Admin can reset all message data (Stats) from Settings (type RESET).
- **Acrophobia** — 4–5 letter random acronyms (huge combo space).
- **DMs** — In channel list only (no right-side drawer); Message opens DM from context menu.
