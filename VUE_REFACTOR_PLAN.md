# ChitChat Vue 3 Refactor Plan

CDN-based Vue 3 (Composition API), no build step. Flask backend unchanged.

---

## Phase 1: Core Reactive States

### Primary State (drives main UI)

| State | Type | Source | Description |
|-------|------|--------|-------------|
| `messages` | `ref([])` | room_joined, new_message, older_messages, message_edited, message_deleted, messages_deleted | Messages in current room |
| `currentRoom` | `ref(null)` | room_joined, switchRoom, rooms_updated | Active room/channel |
| `allRooms` | `ref([])` | room_joined, rooms_list, rooms_updated, room_created, room_deleted, dm_room | All rooms + DMs |
| `roomOrderIds` | `ref([])` | rooms_list, rooms_updated, save_room_order | User's room order |
| `allUsersWithStatus` | `ref([])` | room_joined, user_list_updated | Users with online status |
| `showingSettings` | `ref(false)` | Settings toggle | Whether Settings view is visible |
| `stats` | `ref(null)` | room_joined (Stats room) | Stats view data when in Stats room |

### Connection & Status

| State | Type | Source | Description |
|-------|------|--------|-------------|
| `status` | `ref('Connecting…')` | connect, disconnect, connect_error, error | Connection status text |
| `connected` | `ref(false)` | connect, disconnect | Socket connected? |
| `sendBtnDisabled` | `ref(true)` | connected | Derived from connected |

### Unread & Notifications

| State | Type | Source | Description |
|-------|------|--------|-------------|
| `unreadRooms` | `ref({})` | room_joined, new_message, unread_incremented, rooms_list | room_id → true |
| `unreadMentions` | `ref({})` | user_mentioned, room_joined | room_id → Set of message_id |
| `roomNotificationMuted` | `ref({})` | room_joined, room_notification_mute_updated | room_id → true |

### Room-Specific

| State | Type | Source | Description |
|-------|------|--------|-------------|
| `roomMutedInRoom` | `ref({})` | room_joined, room_muted_updated | room_id → Set of muted user_ids |
| `hasMoreMessages` | `ref(false)` | room_joined, older_messages | Pagination: more history? |
| `typingUsers` | `ref({})` | user_typing (with 5s timeout) | user_id → { username, timeout } |

### Acrophobia

| State | Type | Source | Description |
|-------|------|--------|-------------|
| `acroPhase` | `ref('idle')` | room_joined, acrophobia_phase | submitting | voting | idle |
| `acroEndTime` | `ref(null)` | room_joined, acrophobia_phase | Unix timestamp |
| `acroAcronym` | `ref(null)` | room_joined, acrophobia_phase | Current acronym |
| `acrobotActive` | `ref(true)` | acrobot_status |
| `homerActive` | `ref(true)` | homer_status |

### Modals & UI State

| State | Type | Source | Description |
|-------|------|--------|-------------|
| `profileModal` | `ref(null)` | user_profile | User to show in profile modal |
| `whoisModal` | `ref(null)` | whois_result | Whois data |
| `editMessageModal` | `ref({ id, content } \| null)` | Edit message flow |
| `editProfileModal` | `ref(false)` | Edit profile flow |
| `editRoomModal` | `ref(null)` | Edit room flow |
| `reactionPicker` | `ref({ msgId, anchorEl } \| null)` | Reaction picker state |
| `contextMenu` | `ref({ x, y, target } \| null)` | User/room/message context menu |
| `searchResults` | `ref(null)` | search_results | Search results modal |
| `roomSwitcherOpen` | `ref(false)` | Room switcher modal |
| `toasts` | `ref([])` | showPingToast, away_message, etc. | Toast notifications |

### Settings & Config

| State | Type | Source | Description |
|-------|------|--------|-------------|
| `messageRetentionDays` | `ref(null)` | room_joined, message_retention_updated | 7 | 30 | 90 | null |
| `rolePermissions` | `ref({})` | role_permissions | Super Admin config |
| `auditLogEntries` | `ref([])` | audit_log | Audit log data |
| `defaultRoomId` | `ref(null)` | role_permissions | Default channel |
| `settingsPendingSettings` | `ref({})` | Settings form dirty state |

### Reply & Input

| State | Type | Source | Description |
|-------|------|--------|-------------|
| `replyToMessageId` | `ref(null)` | Reply button | Message we're replying to |
| `replyToContent` | `ref('')` | | |
| `replyToDisplayName` | `ref('')` | | |
| `inputValue` | `ref('')` | v-model on textarea | Message input |

### Local Storage / Non-Reactive Helpers

| Item | Storage | Description |
|------|---------|-------------|
| `hiddenMessageIds` | localStorage | User-hidden messages |
| `messagesSectionHeight` | localStorage | Resizable panel height |

### Constants (from Flask template)

| Constant | Source |
|----------|--------|
| `currentUserId` | `{{ user.id }}` |
| `currentUsername` | `{{ user.username }}` |
| `currentUserStatusLine` | `{{ user.status_line }}` |
| `currentUserAwayMessage` | `{{ user.away_message }}` |
| `isSuperAdmin` | `{{ user.is_super_admin }}` |
| `userPermissions` | `{{ user_permissions }}` |
| `socketPollingOnly` | `{{ socket_polling_only }}` |

---

## Phase 2: Structure

### Vue App Mount

- Mount point: `#app` wrapping the main chat layout (or keep existing structure, mount on a wrapper div).
- Use `createApp()` from Vue 3 CDN.
- Pass constants as `app.config.globalProperties` or via `provide/inject`.

### Socket.IO Integration

- Create `useSocket()` composable or a single `setupSocket(app)` that:
  1. Creates socket: `io({ withCredentials: true, transports: [...] })`
  2. Registers all `socket.on()` handlers
  3. Each handler updates Vue reactive state (e.g. `messages.value = data.history`)
  4. Emit via `socket.emit()` (unchanged)

### Key Mappings (Socket event → State update)

| Event | State Updates |
|-------|---------------|
| `connect` | status, connected, sendBtnDisabled |
| `disconnect` | status, connected |
| `connect_error` | status |
| `room_joined` | currentRoom, messages, allRooms, roomOrderIds, allUsersWithStatus, stats, hasMoreMessages, roomMutedInRoom, unreadRooms, unreadMentions, roomNotificationMuted, acroPhase, acroEndTime, acroAcronym, showingSettings=false |
| `new_message` | append to messages if current room; else unreadRooms |
| `older_messages` | prepend to messages, hasMoreMessages |
| `message_edited` | update message in messages |
| `message_deleted` | remove from messages |
| `messages_deleted` | remove multiple from messages |
| `user_list_updated` | allUsersWithStatus |
| `rooms_list` | allRooms, roomOrderIds, unreadRooms, roomNotificationMuted |
| `rooms_updated` | allRooms, roomOrderIds, refresh currentRoom |
| `room_created` | append to allRooms |
| `room_deleted` | remove from allRooms, roomOrderIds |
| `dm_room` | add/update in allRooms, switchRoom |
| `user_typing` | typingUsers (with timeout) |
| `reaction_updated` | update message.reactions in messages |
| `topic_updated` | update room.topic in allRooms, currentRoom |
| `acrophobia_phase` | acroPhase, acroEndTime, acroAcronym |
| `acrobot_status` | acrobotActive |
| `homer_status` | homerActive |
| ... | (see full list in chat.html) |

---

## Phase 3: Componentization

### Logical Components (within single file, using Vue's component option)

| Component | Template | Props | Emits |
|-----------|----------|-------|-------|
| `ChatHeader` | Header bar, logo, channel name, settings/logout | currentRoom, status, connected | — |
| `RoomList` | Room list + DM list | allRooms, roomOrderIds, currentRoom, unreadRooms, unreadMentions | selectRoom, deleteRoom, editRoom |
| `MessageList` | Messages container | messages, currentRoom | loadMore, addReaction, editMessage, reply |
| `MessageItem` | Single message | msg, isOwn, isHidden | react, edit, reply, hide |
| `MessageForm` | Input + send + attach | inputValue, replyTo, disabled | send, attach |
| `UserList` | Online/offline users | allUsersWithStatus, currentRoom | — |
| `SettingsView` | Settings panel | (many) | — |
| `StatsView` | Stats room content | stats | — |
| `ChannelTopic` | Topic bar | currentRoom | — |
| `TypingIndicator` | "X is typing" | typingUsers | — |
| `AcroTimer` | Acrophobia countdown | acroPhase, acroEndTime | — |
| `ModalBackdrop` | Backdrop for modals | visible | — |
| `ProfileModal` | User profile | user | close |
| `WhoisModal` | Whois result | data | close |
| `EditMessageModal` | Edit message | msg | save, cancel |
| `EditProfileModal` | Edit profile | | save, cancel |
| `EditRoomModal` | Edit channel | room | save, cancel |
| `ReactionPicker` | Emoji picker | msgId, position | select, close |
| `ContextMenu` | Right-click menu | x, y, type, target | action |
| `Toast` | Toast notification | message, type | — |
| `MobileBottomNav` | 3-tab mobile nav | activeTab | switchTab |
| `SearchResultsModal` | Search results | results, query | close |
| `RoomSwitcherModal` | Room switcher | rooms, filter | select, close |

### Template Structure (simplified)

```html
<div id="app">
  <ChatHeader />
  <div class="main">
    <RoomList />
    <section class="chat-area">
      <ChannelTopic v-if="currentRoom && !showingSettings" />
      <SettingsView v-if="showingSettings" />
      <StatsView v-else-if="currentRoom?.name === 'Stats'" />
      <MessageList v-else />
      <TypingIndicator />
      <AcroTimer />
      <MessageForm />
    </section>
    <UserList />
  </div>
  <MobileBottomNav />
  <ProfileModal />
  <WhoisModal />
  <!-- ... other modals -->
</div>
```

---

## Implementation Order

1. **Phase 2 first**: Add Vue CDN, create app with reactive state, wire Socket.IO to update state. Keep existing DOM initially; verify state updates correctly. ✅ **DONE**
2. **Phase 3 incrementally**: Replace one section at a time (e.g. RoomList → MessageList → MessageItem) with Vue templates, testing as we go. ✅ **DONE** (TypingIndicator, ChannelTopic, RoomList, UserList, Messages, Stats, Settings)
3. **Cleanup**: Remove dead code, ensure all event handlers use Vue state. ✅ **DONE**

---

## Phase 3 Implementation (Completed)

- **TypingIndicator**: Reactive computed `typingText` from `state.typingUsers`; removed `updateTypingIndicator()`
- **ChannelTopic**: Computeds `channelTopicHtml`, `channelTopicEmpty`, `mobileRoomName`, `showChannelTopic`; removed `renderChannelTopic()` and `updateMobileRoomName()`
- **RoomList**: Vue v-for over `channelsInOrder` and `dmsInOrder`; click, edit, delete, drag-and-drop handlers
- **UserList**: Vue v-for over `onlineUsers` and `offlineUsers`; removed `renderUserList()`
- **Modals (Vue)**: Profile, Whois, Edit Message, Edit Profile, Edit Room, Search Results, Room Switcher — all use `v-if` and reactive state (state.profileModalUser, state.whoisModalData, etc.) instead of imperative DOM
- **Room Switcher**: Vue v-for over `roomSwitcherFiltered`; keyboard nav (↑↓ Enter Esc); Ctrl+K to open
- **Unread indicators**: Removed redundant DOM manipulation in addUnreadForRoom/clearUnreadForRoom; Vue reactivity handles display
- **window.chitchat**: Exposes switchRoom, editRoom, deleteRoom, socket, showProfileModal, showWhoisModal, showSearchResultsModal, showEditMessageModal, showEditProfileModal, openRoomSwitcher, hideAllContextMenus, and settings helpers
- **App mount**: `chitchatApp.mount('#app')` runs after IIFE so `window.chitchat` is available

---

## Phase 2 Implementation (Completed)

- **Vue 3 CDN** added (`vue.global.prod.js`)
- **#app wrapper** around main content (context menus, modals, header, status, main, mobile nav)
- **Reactive state** in `state` object: currentRoom, allRooms, roomOrderIds, allUsersWithStatus, showingSettings, messages, hasMoreMessages, typingUsers, unreadRooms, unreadMentions, roomNotificationMuted, roomMutedInRoom, stats, acroPhase, acroEndTime, acroAcronym
- **Refs**: status, connected
- **Status bindings**: `{{ status }}` on desktop and mobile status divs
- **Socket handlers** updated to mutate `state.*` and `status.value` instead of local variables
- **setStatus** / **setConnected** update Vue refs; DOM updates reactively
- **setAcroPhase** uses state.acroPhase, state.acroEndTime, state.acroAcronym
- **Modals and Room Switcher**: Converted to Vue v-if templates; show/hide via state updates

---

## Files to Modify

- `app/templates/chat.html` — Only file to change. Add Vue CDN script, restructure script block, convert HTML to Vue templates.

## Files NOT to Modify

- All Flask routes, sockets.py, models, etc. — Backend unchanged.
