# ChitChat — Plus-up ideas

Quick list of features and polish that could make the app even better. Pick and choose.

---

## Polish & UX

- **Message reactions** — One-tap emoji reactions on messages (e.g. 👍 😂). *(done)*
- **Edit / delete own message** — Small "edit" / "delete" on your messages with short time window (e.g. 5 min).
- **Unread indicators** — Badge or bold room name when there are new messages since last view. *(done)* "mark as read".
- **Sound** — Optional ping sound when mentioned or DM'd (excluded for now per your request).
- **Theme** — Light/dark toggle or accent color in Settings. *(done)*
- **Keyboard shortcuts** — e.g. Ctrl+K to focus search/room switcher, Esc to close modals. *(done)*

---

## Social & presence

- **Typing indicators** — "User is typing…" in the current channel or DM.
- **Status** — Beyond away: "busy", "do not disturb", custom status line.

---

## Channels & content

- **Search** — Search messages in current room or all rooms. *(done — in-room search; mobile: in hamburger menu)*
- **File uploads / images** — **Implemented** (instance/uploads/; ephemeral on redeploy). 
---

## Acrophobia & games

- **Acro history** — Last N acronyms in this channel so repeats are less likely (optional).
- **Timer display** — Countdown in UI for submit/vote phase (e.g. "45s left").
- **Other minigames** — Trivia, word chain, or a second bot in another channel.

---

## Moderation & admin

- **Audit log** — Super Admin view: who created/deleted rooms, kicked users, reset stats (store in DB or log file). *(done)*
- **Rate limits** — Throttle messages per user per minute to avoid spam. *(done)*

---

## Dev & ops

- **Health endpoint** — e.g. `GET /health` for uptime checks when you deploy. *(done)*

---

## Already in place (for reference)

- **@mention highlights & tab flashing** — When someone @mentions you: message pulse, room badge, tab title flash when tab is hidden. **Global** (all rooms, DMs, Acrophobia).
- **Link previews** — OG image + title/description for URLs in messages; minimize per preview. **Global** (all rooms, DMs, Acrophobia).
- **/help** — Lists all slash commands in channel.
- **Stats reset** — Super Admin can reset all message data (Stats) from Settings (type RESET).
- **Acrophobia** — 4–5 letter random acronyms (huge combo space); L'il Bro/Homey nicknames; vote ack; 15s countdown urgency.
- **Homer** — Type !Simpsons in any room for a random Simpsons quote; online/offline toggle in Settings.
- **DMs** — In channel list only (no right-side drawer); Message opens DM from context menu.
