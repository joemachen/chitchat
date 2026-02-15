# Release notes

## v1.10.0 — SocketIO fix, mobile footer, faster channel switch

**Flask-SocketIO 5.x compatibility**
- **Broadcast fix** — Replaced context `emit(..., broadcast=True)` with `socketio.emit(..., broadcast=True)` throughout. Fixes "unexpected keyword argument 'broadcast'" error when deleting users or performing other broadcast operations.

**Mobile**
- **Drawer footer** — Room list drawer bottom clearance increased to 108px so Search, Settings, and Log out are fully visible above the 3-tab nav bar.

**Channel switching**
- **Optimistic UI** — Room list selection, header, and loading state update immediately on click; content loads in as it arrives.
- **Deferred presence** — Presence broadcast on room join is deferred so the joining user receives room content first.

---

## v1.9.0 — Delete user fix, Send message, mobile drawer

**Delete account & delete user**
- **RoomMute FK fix** — Delete user and delete account now clear RoomMute rows for DM rooms before deleting them, fixing foreign key violations that prevented deletion.
- **Error handling** — Delete user now catches exceptions, rolls back, and shows a clear error message instead of failing silently.

**Context menus**
- **Send message** — Right-click or long-press on a username (user list, messages, header) or on someone's message to open "Send message". Creates a new DM or opens the existing one and switches to it.
- **User menu** — "Message" renamed to "Send message".
- **Message menu** — Added "Send message" when right-clicking on another user's message.

**Mobile**
- **New Room button** — The room list drawer now ends above the bottom nav bar, so the New Room button and footer (Search, Settings, Log out) are no longer hidden underneath it.

---

## v1.8.0 — Message hover position & Acrophobia polish

**Message hover bar**
- **Top-right placement** — Reaction, edit, and reply icons now appear on the top-right of each message (was top-left). Light theme styling updated for the new position.

**Acrophobia**
- **Submission countdown urgency** — The submission countdown now matches the vote countdown: color change and "Hurry!" when 15 seconds or less remain.
- **Vote receipt acknowledgment** — AcroBot announces "A vote has been received." in the Acrophobia room when votes come in, same as for submissions.
- **Full round results** — At the end of each round, AcroBot shows a complete list of submissions with vote counts (e.g. "**1.** \"phrase\" by **username** — X vote(s)") before the winner announcement.
- **Multi-round tally** — When there are multiple rounds, AcroBot keeps an ongoing total votes tally between rounds and adds some smack talk (e.g. "Don't get too comfortable.", "The crown is still up for grabs.").

---

## v1.7.0 — Message hover overlay & sidebar layout

**Message hover bar (desktop)**
- **No height change** — The reaction/edit/reply menu now overlays the top of each message instead of appearing below it. Messages no longer shift or resize on hover.
- **Transparent overlay** — The bar sits at the top of the message with a semi-transparent gradient and backdrop blur, so content remains visible underneath.
- **Smooth fade-in** — Opacity transition for a subtle appearance.

**Sidebar layout**
- **Rooms & Messages sections** — Both sections now fill the full horizontal and vertical space in the sidebar. List items span the full width; no more empty gaps.
- **Desktop and mobile** — Layout fixes apply to both the desktop sidebar and the mobile drawer when opened via the bottom nav.

---

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
