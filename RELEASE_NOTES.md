# Release notes

## v1.6.0 — Mobile bottom navigation

**Mobile navigation**
- **3-tab bottom bar** — On screens under 768px, the side-drawer is replaced by a fixed bottom navigation bar with **Rooms**, **DMs**, and **Settings**.
- **Rooms tab** — Opens the drawer showing group channels.
- **DMs tab** — Opens the drawer showing direct messages.
- **Settings tab** — Opens the Settings view directly.
- **Ergonomics** — 48×48px tap targets, 60-30-10 color rule (active 100% opacity, inactive 60%), safe-area padding for notched devices.
- **OLED-safe** — Uses dark gray (#18181c) instead of true black to reduce smearing.

**Desktop unchanged**
- Above 768px, the existing sidebar layout remains (room list, chat area, user list).

---

## v1.5.0 — Edit profile, away message & channel topic

**Edit profile**
- **Right-click or long-press your name** (header, user list, or your messages) to open the context menu. Choose **Edit profile** to set your status (shown in whois) and away message.
- **Status** — Same as `/status`; appears in whois and profile.
- **Away message** — Same as `/away`; announces in System Events when set or cleared; auto-replies to DMs when someone messages you while away.

**Edit channel**
- **Right-click a channel** → Edit channel. You can now edit both the **channel name** and **topic** in the modal (previously only name).

**Cross-platform**
- Works on Linux Mint (Firefox), iOS (Safari), Android (Chrome), and Windows. Long-press on touch devices opens the same context menus as right-click.

---

## v1.4.0 — Modals, Whois & bot kick

**Edit channel modal**
- **Styled modal** — Edit channel name now uses an app-themed modal (like edit message) instead of the native browser prompt. Dark/light theme support, Enter to submit, Esc to close.

**Context menus**
- **Whois replaces View profile** — Right-click on a username (in messages or user list) now shows Whois instead of View profile. Whois shows account info, online status, IP, connected time, shared rooms.

**AcroBot & Homer**
- **Kick restricted** — Only Surfer Girl can kick AcroBot or Homer. Users with kick_user permission can kick other users but not system bots.

**Cross-browser**
- **Form controls** — Consistent appearance for buttons, inputs, and textareas across browsers and devices.

---

## v1.3.0 — Users panel, links & protected channels

**Users panel**
- **Current room hidden for you** — Your own entry no longer shows "in &lt;room&gt;" (e.g. "in Sports & Gambling Tips"); other users still see each other's current room.

**Links & images**
- **Mint Linux Firefox** — Link and image clicks now behave the same as on other systems (explicit `window.open` for consistent new-tab behavior).

**Protected channels**
- **Rename restricted** — Only Surfer Girl can rename protected channels. Room owners and users with edit permission can no longer rename protected channels.

---

## v1.2.0 — Status, reactions & deploy notes

**Status from right-click menu**
- **Set status** — Right-click your name (header, user list, or your messages) to set Online, Away, Do Not Disturb, or Invisible.
- **Invisible** — Appear offline to others while still using the app.

**Reactions & fixes**
- **Robot emoji** — 🤖 added to the reaction picker.
- **Unread dot fix** — No longer shows unread for a room you just left after sending a message.
- **Firefox/Linux** — Edit message modal focus fixed for Firefox on Linux (e.g. Mint).

**Deploy announcements**
- System Events now includes release notes when a new version is deployed.

---

## v1.1.0 — Message input & edit UX

**Message input**
- **Shift+Enter for line breaks** — Enter sends; Shift+Enter inserts a new line. Multi-line messages supported.
- **Auto-resizing textarea** — Input grows as you type (up to 8 lines).

**Edit message modal**
- **Styled modal** — Replaces the native prompt with an app-themed dialog (dark/light/high-contrast).
- **Larger textarea** — Full message visible (120–280px height), no truncation.
- **Keyboard shortcuts** — Enter to save, Shift+Enter for new line, Esc to cancel.

---

## v1.0.0 — Reactions & chat history

**Message reactions**
- **Full emoji library** — Reaction picker now includes ~150 emojis across hands, hearts, smileys, animals, food, activities, and more (was 7).
- **Reaction tooltip** — Hover over an emoji reaction to see which users reacted (e.g. "👍 — alice, bob, carol").

**User chat history control**
- **Delete all my messages** — Settings → Chat history → "Delete all my messages now" (with confirmation).
- **Auto-delete** — Set messages to auto-delete after 7, 30, or 90 days. Cleanup runs on app startup.
