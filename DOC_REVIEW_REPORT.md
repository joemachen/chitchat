# Documentation Review Report

**Date:** 2026-02-15  
**Status:** All fixes applied ✓

## Summary

Several documentation files were outdated. Key gaps addressed: Vue migration reflected in TECH_STACK, ARCHITECTURE, ROADMAP; migration count corrected (001–017); data model completed; socket events table updated; "vanilla JS" references replaced with Vue 3.

---

## 1. TECH_STACK.md

| Issue | Current | Should be |
|-------|---------|-----------|
| Frontend | "Vanilla JS" | Vue 3 (CDN), Composition API, reactive state |
| Chat UI description | "used in app/templates/chat.html" | Vue 3; marked.js for Markdown; Socket.IO client |

---

## 2. ARCHITECTURE.md

| Issue | Current | Should be |
|-------|---------|-----------|
| Migrations | "versions/001..013" | versions/001–017 |
| chat.html | "Vanilla JS" | Vue 3 |
| UI section | "Vanilla JS, Socket.IO client, marked.js" | Vue 3 (Composition API), Socket.IO, marked.js |
| Procfile | "web: python gunicorn_run.py" | ✓ Correct |

---

## 3. TECHNICAL_OVERVIEW.md

| Issue | Current | Should be |
|-------|---------|-----------|
| Migrations | "001–015" | 001–017 |
| User model | Lists room_order_ids, is_super_admin, away_message only | Add: rank, display_name, status_line, user_status, last_seen, message_retention_days |
| Room model | Missing is_protected | Add is_protected |
| Message model | Basic fields only | Add: parent_id, edited_at, attachment_url, attachment_filename, link_previews |
| models.py summary | "User, Room, Message, AcroScore, AppSetting, IgnoreList" | Add: MessageReaction, UserRoomRead, UserRoomNotificationMute, MessageReport, AuditLog, RolePermission, RoomMute |
| chat.html description | "renderRoomList, switchRoom" | Vue templates; renderRoomList removed |
| Section 11 | "Single template with vanilla JS" | Vue 3 (CDN), no build step |
| Socket events table | Missing delete_user, delete_my_messages, set_message_retention, edit_message, delete_message, etc. | Add key user-facing events |
| Settings description | "Theme (Dark/Light)" | Add: Appearance tab, Notifications tab, Chat history (delete/auto-delete), high-contrast |

---

## 4. ROADMAP.md

| Issue | Current | Should be |
|-------|---------|-----------|
| Stack | "Vanilla JS" | Vue 3 (CDN) |
| Migrations | "001–015" | 001–017 |
| Phase 2 | "Optional edit/delete own message" | Edit/delete done |
| Next up #2 | "Keyboard shortcuts — Ctrl+K room switcher, Esc close modals" | Done — mark as *(done)* |

---

## 5. README.md

| Issue | Severity |
|-------|----------|
| No mention of Vue | Low — README is user-facing; Vue is implementation detail |
| No mention of Ctrl+K room switcher | Low — nice-to-have shortcut |
| Context menu "Send message" | ✓ Mentioned |

---

## 6. RELEASE_NOTES.md

| Status |
|--------|
| ✓ Vue migration added to v2.0.0 |
| ✓ v2.1.0 entries correct |

---

## 7. VUE_REFACTOR_PLAN.md

| Status |
|--------|
| ✓ Up to date with completed refactor |

---

## 8. IDEAS.md

| Status |
|--------|
| No critical updates needed |
