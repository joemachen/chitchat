# Release notes

## v3.5.22 — Spoilers

**Spoilers**
- **Syntax** — Wrap text or image URLs in `||double pipes||` (e.g. `||spoiler text||` or `||https://image.png||`).
- **Frosted overlay** — Hidden content shows a blur overlay until clicked; click to reveal.
- **Reveal all** — One-click button unveils every spoiler in the room when any exist.
- **Image support** — PNG, JPG, GIF, WebP, SVG; imgur, ibb.co, Discord CDN; Tenor/Giphy use media proxy.
- **Accessibility** — Keyboard (Enter/Space) and screen-reader support.

---

## v3.5.18 — Hide Get the app button in standalone

**Login page**
- **Get the app** — Button now hidden when viewed in the standalone app (pywebview); only shown in browser. Avoids redundant "get the app" prompt for users already using the app.

---

## v3.5.17 — Homer welcome DM, login Get the app, more quotes

**Homer bot**
- **Welcome DM** — On first login, Homer sends a welcome DM with tips (/help, !Simpsons, Trivia room). Uses `welcome_sent` on User (migration 027).
- **Monthly quote DM** — If user has been away 30+ days (last_seen), Homer sends a random quote DM on reconnect.

**Login page**
- **Get the app** — "⬇ Get the app" button below server status; links to GitHub releases (standalone builds) in new tab. Simpsons yellow styling.

**Homer quotes**
- 30 new Simpsons quotes added to SIMPSONS_QUOTES.

---

## v3.5.16 — Standalone update check

**Standalone window**
- **Update check** — On startup, a background thread fetches the latest release from the GitHub API. If a newer version exists, a dismissible banner appears at the top: "Update available: vX.X.X — Download". Clicking Download opens the releases page in the system browser. Fails silently on timeout or error; retries banner injection up to 3 times for slow page loads.

---

## v3.5.15 — Stats leaderboard query fix

**Stats**
- **Acrophobia & Trivia leaderboards** — Bot exclusion filter now applied before `.limit()` in SQLAlchemy queries. Fixes forbidden filter-after-limit order that could cause errors or incorrect results.

---

## v3.5.14 — Linux standalone build

**Build**
- **Linux** — Added `build-linux` job to GitHub Actions. On tag push (`v*`), builds NoHomersClub-Linux on ubuntu-latest via PyInstaller; uploads to GitHub Releases alongside Windows and macOS.

---

## v3.5.13 — macOS build icon fix

**Build**
- **Pillow** — Added Pillow to macOS PyInstaller build for icon.ico → .icns conversion. Fixes missing app icon on macOS standalone builds.

---

## v3.5.12 — Standalone cookie persistence, build icon

**Standalone window**
- **Cookie persistence** — Session cookie now survives app restarts. Uses `private_mode=False` and platform-specific `storage_path` (e.g. `%APPDATA%\NoHomersClub` on Windows).

**Build**
- **Icon** — `--icon=icon.ico` added to Windows and macOS PyInstaller builds in GitHub Actions. Requires `icon.ico` in project root.

---

## v3.5.11 — GitHub Actions standalone builds

**CI/CD**
- **build-standalone.yml** — On tag push (`v*`), builds Windows (NoHomersClub.exe) and macOS (NoHomersClub-Mac) via PyInstaller; uploads both to GitHub Releases.

---

## v3.5.10 — WebSocket default, standalone Koyeb wrapper

**WebSocket**
- **Default** — `SOCKET_POLLING_ONLY` now defaults to False; WebSocket is attempted in production. Rollback: set `CHITCHAT_SOCKET_POLLING_ONLY=1` in Koyeb environment if WebSocket fails.

**Standalone window**
- **Koyeb-only** — `run_standalone.py` now opens the Koyeb-hosted app in a pywebview window; no local Flask server. Build exe: `run-standalone.bat build` (PyInstaller with icon).

**Other**
- `.gitignore` — Added `dist/`, `build/`, `*.spec`.

---

## v3.5.9 — Auto-delete HTTP API, dead code removal

**Auto-delete (message retention)**
- **HTTP API** — Auto-delete now uses POST `/api/set-message-retention` instead of socket; explicit Save button in Settings → Chat history.
- **API robustness** — Settings API calls use `url_for()` for URLs and handle non-JSON (HTML) responses gracefully.

**Vue 3 settings**
- **Direct method calls** — Settings handlers (Mute all, Delete my messages, AcroBot toggle, etc.) now call methods directly instead of `window.chitchat.*`; Vue 3 templates no longer depend on `window` for event handlers.

**Dead code removal**
- **Socket handlers removed** — `set_message_retention`, `set_super_admin`, `set_user_rank`, `get_bot_channels`, `get_user_profile` (client used HTTP APIs or never called these).
- **Client** — Removed `socket.on('user_profile')` listener; removed unused JS (`moveRoomInOrder`, `settingsPendingSettings`, `lastReadByRoom`, `isMessageUnread`).

---

## v3.5.8 — Cloudinary image fix, auto-delete persistence

**Cloudinary**
- **Attachment URLs** — send_message now accepts Cloudinary URLs (https://res.cloudinary.com/...) in addition to local /uploads/; images uploaded to Cloudinary render correctly in chat.

**Auto-delete (message retention)**
- **Persistence fix** — Setting now persists across logout/login. Uses direct DB UPDATE in socket handler and refresh in chat route to avoid Flask-SocketIO session context issues.

---

## v3.5.7 — Auto-delete settings sync and Vue select fix

**Auto-delete (message retention)**
- **room_joined payload** — Server now includes `message_retention_days` when you join a room (stats or regular). Client state stays in sync when switching rooms or reconnecting.
- **Vue v-model** — Auto-delete select now uses `v-model` instead of `:value`/`@change`; Vue correctly binds to `<option value>` strings.
- **Watch-based save** — Selecting a retention value triggers a Vue watch that emits to the server immediately; no separate change handler.

---

## v3.5.6 — Message edit on mobile, Giphy lightbox fix, modal focus

**Message editing (mobile & cross-browser)**
- **Long-press on messages** — Long-press any message (500ms) to open the context menu (Edit, Reply, Add reaction, etc.) on mobile; matches right-click on desktop.
- **Tap to show edit button** — On mobile, tap your own message to reveal the edit (✎) and reply (↩) buttons; tap elsewhere to hide.
- **Raw content for Edit** — Edit modal now uses the original message content (preserves markdown like **bold**) instead of rendered text.
- **Modal focus** — Edit message modal focus hardened for Firefox, Safari, Opera, and Linux Mint; retries focus via requestAnimationFrame when needed.

**Giphy lightbox**
- **Referer by host** — Media proxy now sends `Referer: https://giphy.com/` when fetching from Giphy, `Referer: https://tenor.com/` for Tenor (fixes Giphy media not loading).
- **GIF fallback click** — Added `.msg-inline-videos a img` to the lightbox click handler so GIF fallback images open in the lightbox.

**Tenor/Giphy**
- Media proxy improvements (view-page resolution, binary pass-through, Referer); fetch-blob approach reverted. See `TENOR_GIF_MP4_TROUBLESHOOTING.md`.

---

## v3.5.5 — Role permissions persistence, mobile New room, MP4 inline playback

**Settings → Users - Roles**
- **Save permissions** — Role Permissions table now has explicit Save permissions button; uses POST `/api/set-role-permissions` for reliable persistence (fixes role permission changes not sticking on desktop and mobile).
- **HTTP API** — Role permissions persist via HTTP instead of socket-only; same pattern as Save roles.

**Mobile**
- **+ New room** — Mobile channel list (Rooms tab) now shows + New room button for users with create_room permission; previously only visible in sidebar.

**Chat**
- **MP4 inline playback** — Direct MP4 URLs (e.g. Tenor) now render as inline video with autoplay, loop, muted (like GIFs); previously showed blank when used as img src.

---

## v3.5.4 — Message order fix, role save improvements

**Message order**
- **Cache bug fix** — Room messages loaded from the in-memory cache were incorrectly reversed (newest at top, oldest at bottom). `get_cached_messages` now returns ascending order (oldest first) for display, matching the DB path.

**Settings → Users - Roles**
- **Save rankings** — Explicit Save rankings button to persist role changes; success/error toasts; reverts on failure.
- **HTTP API** — Role changes now use POST `/api/set-user-roles` instead of socket; fixes Vue reactivity and persistence for new users.
- **Tab rename** — Settings tab renamed to "Users - Roles" for clarity.

---

## v3.5.3 — Login server status, bot isolation, AcroBot status

**Login page**
- **Server status** — Fetches `/health` on load; shows "Server online" (green) or "Server offline" (red).
- **Offline handling** — When server is offline: login button disabled, prominent red banner "⛔ 🚨 Server offline for maintenance. Please try again later."

**User list**
- **Discord-style bot isolation** — Bots (AcroBot, Homer, Prof Frink) in separate "Bots — N" section at top; Online/Offline show only real users.
- **APP badge** — Purple pill badge on bots for visual identification.

**AcroBot**
- **Status line** — Seed sets AcroBot's whois status to "QOKPJCKOSJAFHOFASNJK".

---

## v3.5.2 — Prof Frink and Homer quote expansion

**Prof Frink**
- **FRINK_QUOTES** — 48 classic show quotes (Frinkometer, waffle iron soul extractor, Debulking Ray, etc.) added to vocabulary.
- **FRINKISMS** — New exclamations: Glaven!, Hoyvin-mayvin!, Flavin!
- **DM replies** — 40% chance of a random show quote when DMing Prof Frink.
- **Ridicule & hot streaks** — New phrases when nobody gets trivia right or when users hit correct-answer streaks.

**Homer**
- **SIMPSONS_QUOTES** — 26 new quotes from the show (71 total): "Stupid sexy Flanders!", "Me fail English? That's unpossible.", "I have three kids and no money...", "To the Bee-mobile!", "Mmm... organized crime.", etc.
- **HOMER_DM_REPLIES** — 6 new DM replies based on show quotes.

---

## v3.5.1 — System Events history, unread indicator fixes

**System Events history**
- System Events channel now always shows full message history. Room-mute filtering is skipped entirely for System Events so deploy announcements, "came online", "went offline", and other system messages are never hidden.

**Unread indicator (red dot)**
- Red dot now clears correctly when leaving a channel. Root causes fixed:
  - **On join**: `last_message_id` now uses the actual max message id in the room (not the last in filtered history), so muted users' messages no longer cause a phantom unread when you leave.
  - **While viewing**: Server updates `UserRoomRead` when you receive new messages in the room you're viewing.
- Client ignores `unread_incremented` for the room you're currently viewing (defensive guard).

---

## v3.5.0 — Room roles, message cache, Matrix-inspired features

**Room roles**
- **Server-level roles only** — Roles (rookie, bro, fam, super_admin) set by Super Admin in Settings; permissions (create_room, update_room, delete_room, kick_user, etc.) are role-based.
- **Edit/delete** — Room owner or moderator can edit room (e.g. topic); owner can delete (with existing permission checks).

**Last N messages cache**
- **In-memory cache** — Last 100 messages per room cached; join/reconnect uses cache when available for faster response.
- **Cache invalidation** — New messages append; edits update; deletes and wipe clear cache.

**Matrix-inspired**
- **Private user data** — Key/value store per user for preferences (`get_private_data`, `set_private_data`). No new DB columns per setting.
- **Room aliases** — Human-readable aliases (e.g. `#general`, `#acrophobia`) resolve to room IDs. Join by alias: `join_room({ alias: "general" })`.
- **Payload validation** — Reject messages over 50KB (Matrix-inspired size limit).

---

## v3.4.0 — Prof Frink trivia fixes, set-seasons alias

**Prof Frink trivia**
- **Answer period** — Trivia questions now allow 45 seconds to answer (was 30).
- **Multi-round timeout fix** — When a user answered correctly in a multi-round game, the previous round's timeout could fire and prematurely end the next round. Each round now gets the full 45 seconds.
- **!set-seasons alias** — `!set seasons 1 2 3` and `/set seasons 1 2 3` now work as aliases for `!set-seasons` (space instead of dash).

---

## v3.3.0 — Koyeb deployment fixes, gevent, migration robustness

**Deployment (Koyeb)**
- **Gevent** — Switched from eventlet to gevent for SocketIO async mode (eventlet deprecated in Gunicorn 26, RLock issues on Python 3.13).
- **Gunicorn launcher** — `gunicorn_run.py` now runs gunicorn via subprocess with explicit args to avoid Koyeb/buildpack overrides (`main:app`, `eventlet`).
- **Migrations** — Run in subprocess with 45s timeout; non-fatal on failure so app can start; optional `CHITCHAT_SKIP_MIGRATIONS=1` for debug.
- **Migration 022** — Added `022_room_bot_permissions` to fix DB alembic_version mismatch when schema was migrated with a removed revision.
- **App context** — Fixed "Working outside of application context" when `gevent.spawn_later` deferred user-list broadcast in room join.
- **DB connect timeout** — Added 30s connect timeout for Neon PostgreSQL.

---

## v3.2.0 — Pinned messages, sidebar username overflow fix

**Pinned messages**
- Fam and Super Admin can pin up to 2 messages per room via right-click → Pin (or Unpin).
- Pinned messages appear in a dedicated section at the top of the room.
- Pinned section hidden in Stats room.

**Sidebar**
- Long usernames (e.g. emails) in the user list now truncate with an ellipsis instead of causing horizontal scrollbars.
- Full name shown on hover via tooltip.

---

## v3.1.0 — Prof Frink improvements, Acrophobia countdown, trivia expansion

**Prof Frink trivia**
- **Ridicule on timeout** — When nobody gets it right, Frink ridicules the room in character before revealing the answer.
- **10-second warning** — Frink announces "10 seconds left!" before time runs out.
- **Timer above input** — Countdown bar (like Acrophobia) shows remaining time in Trivia room; input pulses when ≤10s.
- **Time in announcement** — Trivia questions now end with "You have 30 seconds!"
- **Massive trivia pool** — Expanded from 15 to 400+ questions across all difficulties; 200+ focused on seasons 3–9.

**Acrophobia**
- **Countdown timing** — In-channel countdown announcements (10, 9, 8… 1) now begin at 10 seconds left instead of 15 for both submit and vote phases.

---

## v3.0.0 — Codebase cleanup, documentation refresh

**Dead code removed**
- `_extract_first_url` in link_preview.py (unused)
- `get_frink_difficulty`, `get_frink_seasons` in prof_frink.py (redundant with get_frink_settings)
- Unused `import sys` in logging_config.py

**Documentation**
- TECHNICAL_OVERVIEW: migration range 001–020, added prof_frink.py, link_preview.py, delete_account.html, routes (/upload, /health, /export, /delete-account)
- DOC_REVIEW_REPORT: migration count updated
- IgnoreList model docstring corrected (legacy, cascade delete only)

**Assets**
- Added placeholder logo.png to fix 404s for favicon and logo references

---

## v2.8.6 — Mobile room context menu, reorder, Rooms terminology, GIF autoplay

**Mobile: room context menu**
- Long-press on a room in the rooms list (home view or sidebar drawer) now opens the room context menu with Edit, Mute/Unmute, Move up, Move down, and Unmute users (if any muted).

**Room reordering**
- Room context menu (right-click or long-press) now includes **Move up** and **Move down** for reordering rooms without drag-and-drop. Works on desktop and mobile.

**Rooms terminology**
- User-facing "channel" labels replaced with "Room" throughout the UI (Edit room, Delete room, Room name, Room topic, No rooms, Protected rooms, Default room, Bot rooms, etc.).

**Muted rooms**
- Muted rooms now show a muted speaker emoji (🔇) instead of the word "mute" before the room name.

**Unmute users**
- Room context menu shows "Muted in this room" with Unmute options when you've muted users (e.g. System) in that room. Fixes the case where muting the System user in System Events left no way to unmute.

**GIF links**
- Pasted GIF links (Giphy, Tenor, direct .gif) now render as inline playing GIFs instead of plain links. Giphy/Tenor use video for click-to-pause; others use img.

---

## v2.8.5 — GIF fixes, code artifacts, mobile logout

**GIF links**
- GIF URLs (Giphy, Tenor, direct .gif) no longer show both inline image and link preview card — only the inline GIF is shown.
- Link preview cards are filtered to exclude GIF URLs to avoid duplication.

**Code artifacts**
- Trailing `">` or similar artifacts from pasted HTML (e.g. `href="url">`) are now stripped when rendering URLs, so raw `">` no longer appears in messages.

**Mobile: Log out**
- Log out added to Settings view (scroll to bottom) and to channel list footer (Rooms/DMs tabs; scroll to bottom).
- Footer has padding so it stays visible above the 3-tab bottom nav.

---

## v2.8.4 — Custom modals, UI guidelines

**Custom confirm/alert/prompt**
- Replaced all native `alert()`, `confirm()`, and `prompt()` with in-app modals that match the app theme.
- Message delete, channel delete, report, wipe, user delete, and other destructive actions now use styled confirm dialogs.
- Report message and type-to-confirm prompts (e.g. DELETE_ALL_MY_MESSAGES, RESET) use custom prompt modals.
- Delete account page uses a custom confirm modal instead of native confirm.

**UI guidelines**
- Added `UI_GUIDELINES.md` — design tokens, modal dimensions, accessibility notes, and references to WAI-ARIA.
- Edit modals (message, profile, channel), search results, and room switcher updated for responsive dimensions (desktop and mobile).
- Modals: min-width 280px, max-width calc(100vw - 2rem) on mobile; Escape to close; focus management.

---

## v2.8.3 — Discord-style letter avatars

**Letter avatars**
- **Message cards** — Each message shows a circular avatar with the user's initial and a colored background.
- **User list** — Sidebar and mobile presence sheet show letter avatars with status borders (online/away/dnd/offline).
- **Deterministic colors** — When no custom color is set, a stable color is derived from the user ID.
- **Custom color** — Settings → Profile → Avatar color: picker, hex input, Save, Reset.

**Model**
- Added nullable `avatar_bg_color` (hex) to User.

---

## v2.8.2 — Mobile presence bar, Prof Frink rounds, user list cleanup

**Mobile: inline presence bar**
- **Presence bar** — When viewing a room on mobile, a compact "X online" bar appears above the message input. Tap to open a bottom sheet with Online/Offline user list.
- **Bottom sheet** — Swipe-down or tap the handle to dismiss; 44pt tap targets; right-click/long-press on users for Whois, Message, etc.

**Prof Frink**
- **Round X of Y** — Multi-round trivia (`!trivia 3`) now prefixes each question with "Round 1 of 3", "Round 2 of 3", etc.
- **More personality** — Added Frinkisms, hot-streak phrases, and DM replies to keep the bot fresh.

**Desktop**
- **User list** — Removed "in Lobby" (room) display from the online user list.

---

## v2.8.1 — Bug fix, cleanup, help updates

**Bug fix**
- **Bio overwrite** — Edit profile modal (right-click name) no longer clears bio when saving only status/away.

**Cleanup**
- Removed dead code: `get_preview_for_message_content`, `get_submit_end_time`, `get_vote_end_time`; inlined `_broadcast_new_message`; removed prof_frink TODO.
- Documentation: ROADMAP migrations 001–019, mobile channel list; README /nick, /status, /away, /slap; VUE_REFACTOR_PLAN archived; PROFFRINK_PROPOSAL Integration completed.

**Help messages**
- `/help` — Added bio to /whois, Settings → Profile, clarified right-click menus and /nick//status clear syntax.
- Prof Frink help — Channel scope (configured channels), ! and / both work.

---

## v2.8.0 — Profile tab, bio, away message, mobile channel list

**Mobile: channel list replaces profile panel**
- **Back button** — When viewing a channel, tap ← to see the full channel list (Rooms + DMs) with the 3-tab nav. Profile is now in Settings → Profile.
- **Channel list** — Rooms and DMs tabs; tap a channel to open it.

**Settings → Profile tab (desktop)**
- **Profile tab** — New first tab in Settings mirroring the mobile profile panel: Nick, Status, Visibility (Online/Away/DND/Invisible), Away message, Bio/About, Time connected, Member since, Stats preview.
- **Notification preferences** — Per-room mute summary ("X of Y channels muted"), Mute all / Unmute all buttons, link to Notifications tab for per-room control.

**Profile additions**
- **Bio / About** — Short bio (up to 200 chars) shown in whois and profile modals.
- **Away message** — Auto-reply for DMs (Edit profile modal; Profile tab).
- **Notification prefs** — Mute summary and global Mute all / Unmute all in Profile tab.

**Whois modal**
- **Bio** — Bio field shown when present.

---

## v2.7.0 — Mobile navigation redesign, profile home panel

**Mobile navigation**
- **Content view** — When viewing a room, DM, or Settings, the 3-tab bottom nav is hidden to maximize screen space for chat.
- **Back button** — Tap the back arrow (←) or "No Homers Club" area in the header to return to the home panel.
- **Home panel** — Profile-focused view with 3-tab nav visible: edit Nick (display name) and Status, view time connected, member since date, and stats preview (top 5 typers).
- **Flow** — From home, Rooms/DMs open the channel list; selecting a room or tapping Settings switches to full-screen content view.

---

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
