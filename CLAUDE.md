# CLAUDE.md — ChitChat project rules

> **Living document.** When you make a mistake in this repo, add a rule to the relevant section immediately so it is never repeated. Check these rules at the start of every task.

---

## Project overview

ChitChat is a private, invite-only chat app (Discord/mIRC-style) for small groups (~10 users), branded **No Homers Club**. It runs locally (SQLite + browser) or online (Neon PostgreSQL + Koyeb). The single UI template is `app/templates/chat.html` (Vue 3 via CDN).

Current version is tracked in **two places that must always match**:
- `app/version.py` → `VERSION = "x.y.z"`
- `run_standalone.py` → `CURRENT_VERSION = "x.y.z"`

---

## Tech stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11+, Flask 3, Flask-SocketIO, gevent |
| ORM / migrations | Flask-SQLAlchemy, Flask-Migrate (Alembic) |
| Frontend | Vue 3 (CDN), Socket.IO client 4.7.2, marked.js |
| DB (dev) | SQLite (`instance/chitchat.db`) |
| DB (prod) | Neon PostgreSQL via `DATABASE_URL` |
| Deploy | Koyeb (Procfile), GitHub Actions (PyInstaller on `v*` tag) |
| Optional | Cloudinary (uploads), pywebview (standalone window) |

---

## Key commands

```bash
# Run locally (Windows)
run.bat                      # browser mode
run-standalone.bat           # opens Koyeb-hosted app in native window
run-standalone.bat build     # build standalone .exe

# Run manually
python run.py

# Database
flask db upgrade             # apply pending migrations
flask db migrate             # generate migration for schema changes
flask db stamp <rev>         # manually mark migration applied
```

No formal test suite — QA is manual.

---

## Release checklist (do ALL steps, in order)

1. Update `/help` command text in `app/sockets.py` to reflect any new commands
2. Add a release entry to `RELEASE_NOTES.md` at the top (below the `# Release notes` heading)
3. Bump version in **both** `app/version.py` and `run_standalone.py` — they must match
4. Commit everything into one branch → `gh pr create` → `gh pr merge --squash`
5. **Only after the PR is merged:** `git checkout main && git pull origin main` → verify HEAD has the version bump → `git tag vX.Y.Z` → `git push origin main --tags`

> ⚠️ **Never tag before all commits are merged to main.** The tag determines what GitHub Actions compiles — a premature tag produces an exe with the wrong version.

---

## Git / PR conventions

- Merge strategy: **squash** (`gh pr merge --squash`)
- Full automation expected: commit → `gh pr create` → `gh pr merge --squash` — no manual steps
- Never amend published commits; always create new commits
- `gh` CLI is installed and authenticated

---

## Architecture conventions

- **App factory:** `create_app()` in `app/__init__.py` — Flask setup, DB init, migrations, socket registration
- **Migrations auto-run** on startup (also in `gunicorn_run.py` for prod)
- **Message cache:** in-memory, last 100 messages per room — do not bypass it
- **Logging:** file-based only — `logs/app.log` and `logs/errors.log` (not console)
- **All frontend** lives in `app/templates/chat.html` (single-file Vue 3 app)
- **SocketIO events** are in `app/sockets.py`; HTTP routes in `app/routes.py`

---

## UI rules

- **Never use** native `alert()`, `confirm()`, or `prompt()` — always use custom Vue modals
- **z-index:** backdrop `2000`, dialog `2001`, pickers/overlays `2002`
- **Modal width:** max 480px desktop; `calc(100vw - 2rem)` on mobile (≤768px)
- **Touch targets:** minimum 44px height on mobile
- **Button order:** Cancel (left) | OK/Confirm (right); destructive action on the right in destructive color
- **Design tokens:**

| Token | Dark | Light |
|-------|------|-------|
| Surface bg | `#25262b` | `#fafafa` |
| Input bg | `#0f0f12` | `#fff` |
| Border | `#3f3f46` | `#d4d4d8` |
| Text primary | `#e4e4e7` | `#18181b` |
| Accent | `#6366f1` | `#6366f1` |
| Destructive | `#ef4444` | `#dc2626` |

Full reference: `UI_GUIDELINES.md`

---

## Environment variables

| Variable | Required | Notes |
|----------|----------|-------|
| `CHITCHAT_SECRET_KEY` | Yes | Must be non-default; validated at startup |
| `CHITCHAT_INVITE_CODE` | Yes | Must be non-default; validated at startup |
| `CHITCHAT_DATABASE_URI` / `DATABASE_URL` | For prod | Neon PostgreSQL connection string |
| `CLOUDINARY_URL` | No | If set, uploads go to Cloudinary; else `instance/uploads/` |
| `CHITCHAT_SERVER_NAME` | No | Header branding (default: "No Homers Club") |
| `CHITCHAT_MAX_UPLOAD_MB` | No | Default: 5 |
| `CHITCHAT_MESSAGES_PER_MINUTE` | No | Rate limit; 0 = disabled |

Copy `.env.example` to `.env` — never commit `.env`.

---

## Reference docs (read before big changes)

- `TECHNICAL_OVERVIEW.md` — comprehensive technical reference
- `ARCHITECTURE.md` — high-level design
- `TECH_STACK.md` — stack summary
- `UI_GUIDELINES.md` — modal and form standards
- `RELEASE_NOTES.md` — full version history
- `ROADMAP.md` — future plans and backlog

---

## Mistakes and rules (add new ones here)

> When you make a mistake, document it below with a short title and rule so future sessions avoid repeating it.

### [2026-03-19] Vue functions used in template but not returned from setup()
**Rule:** Every function or reactive variable referenced in the `chat.html` Vue template **must** be included in the `return { ... }` block at the end of `setup()`. Missing returns cause a silent render crash → black screen. This has happened twice now (v3.5.38 polls, v3.5.40 link previews). After adding any new function used in the template, always verify it appears in the return object.
