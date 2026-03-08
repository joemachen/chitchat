# Prof Frink Trivia Bot — Proposal & API Analysis

## 1. API Analysis: simpsons-trivia.com

**Finding:** `https://simpsons-trivia.com/api` returns **404**. No public API is currently available.

**Alternatives considered:**
- **thesimpsonsapi.com** — Has `/api/characters`, `/api/episodes`, `/api/locations`. Episodes include `synopsis`; could be used to generate trivia (e.g. "In [episode name], what happens?"). No pre-built trivia Q&A.
- **Placeholder approach** — Use static trivia list in `prof_frink.py` until simpsons-trivia.com exposes an API.

**Proposed API contract** (when simpsons-trivia.com adds an endpoint):

```
GET /api/questions?difficulty=intermediate&season=5&limit=1
Response: {
  "question": "In 'X', who does Y?",
  "answer": "Z",
  "difficulty": "intermediate",
  "season": 5
}
```

Config: `TRIVIA_API_URL = "https://simpsons-trivia.com/api/questions"` in `app/config.py`.

---

## 2. prof_frink.py Service (Implemented)

- **TriviaQuestion** dataclass: `question`, `answer`, `difficulty`, `season`
- **Placeholder data**: 15 Simpsons trivia Q&As; filtered by `!set-difficulty` and `!set-seasons`
- **Personality**: `format_frink_reply()` wraps text with random Frinkisms (Glavin!, Hoyvin!, etc.)
- **State**: `_frink_active`, `_frink_daily_enabled`, `_frink_difficulty`, `_frink_seasons`
- **Commands**: `get_trivia_response()`, `get_help_text()`, `get_frink_settings()`

---

## 3. Integration (Completed)

- [x] **Seed Trivia room** in `_seed_default_data()`: `Room(name="Trivia", is_protected=True)`
- [x] **Add Prof Frink user** in seed (like Homer)
- [x] **Socket integration** in `on_send_message`: when `room.name == "Trivia"`, parse `!trivia`, `!daily`, `!set-difficulty`, `!set-seasons`, `!settings`, `!help`
- [x] **Channel restriction**: Prof Frink responds only in #Trivia (configurable via bot_channels)
- [x] **bot_channels**: `AppSetting` key for Super Admin to configure which channels each bot can respond in (Settings → Bot channels)
- [x] **frink_control permission**: Super Admin toggles Prof Frink in Settings
- [x] **Daily trivia**: eventlet timer posts one question per day at 9:00 UTC when `_frink_daily_enabled`

---

## 4. Command Details

| Command | Who | Action |
|---------|-----|--------|
| `!trivia` | Any | Post one random question (answer revealed after delay or `!answer`) |
| `!daily` | Super Admin | Toggle daily automated post |
| `!set-difficulty X` | Any | Filter: beginner, intermediate, advanced, master |
| `!set-seasons 1 2 3` | Any | Filter by season(s) 1–20 |
| `!settings` | Any | Show current config |
| `!help` / `!commands` | Any | Frink help menu |

---

## 5. Integration Complete

- [x] Analyze simpsons-trivia.com API (404; use placeholder)
- [x] Propose and implement `prof_frink.py` service class
- [x] Integrate with sockets (Trivia room, command parsing)
- [x] Add Prof Frink to Settings UI (toggle, like Homer)
- [x] Add frink_control permission
- [ ] Add bot channel management (Super Admin protocol) — future
