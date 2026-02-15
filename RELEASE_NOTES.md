# Release notes

## v2.6.0 — Accessibility, font picker, mobile layout, context menu

**Accessibility**
- **Toast announcements** — Toasts (pings, reconnected, topic updated, etc.) now use an `aria-live` region so screen readers announce them.
- **Semantic HTML** — Messages wrapped in `<article>`; context menus use `role="menu"` and `role="menuitem"`; header and modals have proper ARIA.
- **Focus management** — Modals focus the first focusable element on open and restore focus on close; room switcher arrows move focus between options.
- **Form labels** — Message input and attach button have `aria-label`; room switcher options have `aria-selected` and `tabindex`.

**Appearance**
- **Font picker** — Settings → Appearance: choose from system fonts (Segoe UI, Inter, Roboto, Helvetica Neue, Arial, Georgia, Verdana, Times New Roman) or use system default.
- **Settings/Log out spacing** — Increased gap between Settings link and Log out button in header and room list footer.

**Mobile**
- **Rooms panel** — Rooms drawer now extends to the bottom of the screen; New room button and Search/Settings/Log out remain visible with safe-area padding.

**Context menus**
- **Screen boundaries** — Context menus (user, room, message, selection) stay within viewport; on mobile, menus avoid the bottom navigation bar.

---

## v2.5.0 — Trivia rounds, bot DMs, hot streaks, scrollbars, UX

**Prof Frink trivia**
- **!trivia X** — Run 1–7 consecutive trivia rounds (e.g. `!trivia 3`). Next question posts 3 seconds after each round ends.
- **Trivia timeout fix** — Answer now reveals after 30 seconds (was 8+ hours due to eventlet seconds vs milliseconds).
- **Hot streaks** — Prof Frink recognizes consecutive correct answers and says something Frink-y (2, 3, 5+ in a row).
- **DM replies** — Message Prof Frink in a DM; he replies with a random Frink-y greeting.

**Homer**
- **DM replies** — Message Homer in a DM; he replies with a Homer-esque message.

**UI**
- **Bot labels** — Bots (AcroBot, Homer, Prof Frink, System) show "(bot)" in the Users list.
- **Dark mode scrollbars** — Scrollbars themed for dark/light mode (room list, user list, messages, modals).

**Admin terminology**
- **Public references** — "Surfer Girl" replaced with "admin" or "Super Admin" in user-facing text; only the super admin sees the internal role name.

---

## v2.4.0 — Bot channel management, trivia in Stats

**Bot channel management**
- **admin config** — Settings → Bot channels: configure which channels AcroBot, Homer, and Prof Frink can respond in. Comma-separated channel names; "all" or empty = all channels. Defaults: AcroBot=Acrophobia, Homer=all, Prof Frink=Trivia.

**Stats channel**
- **Trivia leaderboard** — Stats view now shows Trivia leaderboard (top 10 by correct answers), alongside Acrophobia leaderboard.

---

## v2.3.0 — Trivia scoring, leaderboard, first-correct-wins

**Prof Frink trivia**
- **First correct answer wins** — Type the answer in chat (case-insensitive); first correct message awards a point. Answer revealed immediately on correct guess, or after 30s if no one gets it.
- **TriviaScore & leaderboard** — `!score` or `/score` shows top 10 in the Trivia room. Scores persisted per room per user (like Acrophobia).

---

## v2.2.0 — Prof Frink trivia, daily scheduler, protected save fix, Scrabble acronyms

**Prof Frink trivia bot**
- **Trivia channel** — New #Trivia room with Simpsons trivia bot. Commands: `!trivia`, `!help`, `!settings`, `!set-difficulty [beginner|intermediate|advanced|master]`, `!set-seasons [1-20]`.
- **Daily trivia** — `!daily` (admin or frink_control) toggles automated daily post at 9:00 UTC.
- **Settings** — Prof Frink on/off toggle and `frink_control` permission (like Homer).

**Protected channel save**
- **Settings fix** — Protected channel checkbox in Settings → Channels now saves correctly (optimistic update + room_renamed sync).
- **Edit Room modal** — admin can toggle "Protect channel" when editing a room.

**Acrophobia**
- **Scrabble-weighted acronyms** — Letter distribution now follows Scrabble tile frequencies (E common, Q/Z rare). Same letter rarely repeats twice in a row.

---

## v2.1.0 — Protected channels, delete user fix, chat history

**Protected channel editing**
- **Name edit restricted** — Non–admin users editing a protected channel see "Protected channel names cannot be edited, sucka." instead of the name input. They can still edit the topic.

**Delete user**
- **MessageReaction fix** — Delete user now removes reactions by the deleted user before deletion, fixing the `user_id` null violation on `message_reactions`.

**Chat history**
- **All users** — Settings → General → Chat history (Delete all my messages, Auto-delete) is available to all users; no role restriction.

---

## v2.0.0 — Deploy announcements, unread dot, DB pooling, Vue refactor

**Frontend**
- **Vue 3 migration** — Chat UI refactored from vanilla JS to Vue 3 (Composition API via CDN). Room list, messages, user list, stats, settings, modals (profile, whois, edit message/profile/room, search results, room switcher), and unread indicators now use reactive state. No build step.

**System Events**
- **Version-only announcements** — Release notes are posted to System Events only when a new version is deployed, not on every redeploy. Uses `last_deploy_announced_version` in app settings.

**Unread indicators**
- **Red dot accuracy** — Dot only shows when a room has unread messages. Hidden for the current room, muted rooms, and when there are no unread messages.
- **Badge count** — Title and favicon unread count exclude the current room and muted rooms.

**Reliability**
- **Database pooling** — PostgreSQL engine options: `pool_pre_ping` and `pool_recycle` (300s) to reduce "SSL connection has been closed unexpectedly" errors.
- **Eventlet launcher** — `gunicorn_run.py` runs `eventlet.monkey_patch()` before gunicorn to fix "RLock(s) were not greened" warning.

---

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
- **Kick restricted** — Only admin can kick AcroBot or Homer. Users with kick_user permission can kick other users but not system bots.

**Cross-browser**
- **Form controls** — Consistent appearance for buttons, inputs, and textareas across browsers and devices.

---

## v1.3.0 — Users panel, links & protected channels

**Users panel**
- **Current room hidden for you** — Your own entry no longer shows "in &lt;room&gt;" (e.g. "in Sports & Gambling Tips"); other users still see each other's current room.

**Links & images**
- **Mint Linux Firefox** — Link and image clicks now behave the same as on other systems (explicit `window.open` for consistent new-tab behavior).

**Protected channels**
- **Rename restricted** — Only admin can rename protected channels. Room owners and users with edit permission can no longer rename protected channels.

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
