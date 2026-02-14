"""
Acrophobia game bot (mIRC/AcroBot-style). Hosts rounds: acronym -> submit phrase -> vote -> winner.
State is in-memory per room. Scores are persisted in DB. Bot messages are returned for the socket layer to persist and emit.
Acronyms are 4 or 5 random letters for hundreds of combinations.
"""
import random
import string
import time


def _get_db():
    """Lazy import to avoid circular deps. Use inside Flask app context."""
    from app.models import AcroScore, User, db
    return db, AcroScore, User


def _random_acronym(length: int | None = None) -> str:
    """Return a random 4- or 5-letter uppercase acronym. length 4 or 5, or random if None."""
    if length not in (4, 5):
        length = random.choice((4, 5))
    return "".join(random.choices(string.ascii_uppercase, k=length))

# Game state per room_id: phase, acronym, submissions, votes, end_time
_games = {}

# Super Admins can activate/deactivate the bot in Settings
_acrobot_active = True

SUBMIT_SECONDS = 60
VOTE_SECONDS = 45


def is_acrobot_active() -> bool:
    return _acrobot_active


def set_acrobot_active(active: bool) -> None:
    global _acrobot_active
    _acrobot_active = bool(active)


def _game(room_id):
    if room_id not in _games:
        _games[room_id] = {
            "phase": "idle",  # idle | submitting | voting
            "acronym": None,
            "submissions": [],  # [{"user_id", "username", "phrase"}]
            "votes": {},  # user_id -> index (0-based)
            "end_time": None,
        }
    return _games[room_id]


def _get_help_replies() -> list[str]:
    """Full help text for AcroBot: how to interact, start a game, rules. Returns one message."""
    lines = [
        "**AcroBot — Acrophobia** (acronym phrase game)",
        "",
        "**How to interact** — In this channel you can:",
        "  • Type **/help** or **/msg acrobot help** anytime for this message.",
        "  • Type **/start** to start a new round (when no round is running).",
        "  • During a round: reply with **one message** as your phrase for the acronym.",
        "  • During voting: type **/vote N** (e.g. /vote 1) to vote for submission N.",
        "",
        "**How to start a game** — Any user can type **/start** in this channel. The bot will post a 4- or 5-letter acronym; everyone has a short time to submit a phrase that fits (e.g. ABC → \"A Big Cat\"). Then everyone votes for their favorite; the winner is announced.",
        "",
        "**Rules** — (1) One phrase per person per round. (2) No editing after submit. (3) Vote once during the vote phase. (4) Have fun. Type **/score** for the leaderboard.",
    ]
    return ["\n".join(lines)]


def _phrase_matches_acronym(phrase: str, acronym: str) -> bool:
    """True if the phrase's first letter of each word (case-insensitive) spells the acronym."""
    if not phrase or not acronym:
        return False
    words = phrase.strip().split()
    letters = "".join(w[0] for w in words if w).upper()
    return letters == acronym.upper()


def handle_message(room_id: int, user_id: int, username: str, content: str) -> tuple[bool, list[str], list[tuple[int, str]]]:
    """
    Handle a user message in the Acrophobia room. Returns (consumed, bot_replies, dm_replies).
    bot_replies are messages for the Acrophobia channel; dm_replies is a list of (user_id, text) to send in DM.
    """
    content = (content or "").strip()
    if not content:
        return False, [], []
    g = _game(room_id)
    low = content.lower()

    # Help triggers: /help, /msg acrobot help, !help, acrobot help
    is_help = (
        low == "/help"
        or low == "!help"
        or low == "acrobot help"
        or low.startswith("/m acrobot help")
        or low.startswith("/msg acrobot help")
        or low.startswith("/message acrobot help")
        or low.startswith("!acrobot help")
    )
    if is_help:
        return True, _get_help_replies(), []

    # Submitting phase: /m, /msg, /message acrobot <phrase> or !acrobot <phrase> counts as submission
    _acrobot_prefix = (
        low.startswith("/m acrobot ") or low.startswith("/msg acrobot ") or
        low.startswith("/message acrobot ") or low.startswith("!acrobot ")
    )
    if g["phase"] == "submitting" and _acrobot_prefix:
        idx = low.find("acrobot") + len("acrobot")
        phrase = content[idx:].strip()
        if not phrase:
            return True, [], []
        if any(s["user_id"] == user_id for s in g["submissions"]):
            return True, ["You already submitted this round."], []
        acronym = g["acronym"] or ""
        if not _phrase_matches_acronym(phrase, acronym):
            dm = f"Your phrase doesn't match the acronym **{acronym}**. Use a phrase whose first letter of each word spells that acronym."
            return True, [], [(user_id, dm)]
        g["submissions"].append({"user_id": user_id, "username": username, "phrase": phrase})
        return True, ["A submission has been received."], [(user_id, f"Got it! Your phrase for **{acronym}** has been received.")]

    # /m, /msg, /message acrobot <anything> or !acrobot <anything> — generic reply when not a submission
    if _acrobot_prefix:
        rest = low.split("acrobot", 1)[-1].strip()
        if rest != "help":
            if _acrobot_active:
                return True, ["AcroBot here. Type **/help** or **/msg acrobot help** for commands and rules."], []
            return True, ["AcroBot is currently offline. A Super Admin can activate me in Settings."], []

    # When bot is offline: only respond to game-related input with offline message; /score still works
    if not _acrobot_active:
        if low == "/score":
            return True, _get_score_replies(room_id), []
        if low == "/start" or low.startswith("/vote ") or g["phase"] != "idle":
            return True, ["AcroBot is currently offline. A Super Admin can activate me in Settings."], []
        return False, [], []

    # Commands
    if low == "/start":
        if g["phase"] != "idle":
            return True, ["A round is already in progress. Wait for it to finish."], []
        return True, _start_round(room_id), []
    if low == "/score":
        return True, _get_score_replies(room_id), []

    if g["phase"] == "submitting":
        if low.startswith("/"):
            return True, [], []
        # Submission (plain message in channel)
        if any(s["user_id"] == user_id for s in g["submissions"]):
            return True, ["You already submitted this round."], []
        acronym = g["acronym"] or ""
        if not _phrase_matches_acronym(content, acronym):
            dm = f"Your phrase doesn't match the acronym **{acronym}**. Use a phrase whose first letter of each word spells that acronym."
            return True, [], [(user_id, dm)]
        g["submissions"].append({"user_id": user_id, "username": username, "phrase": content})
        return True, ["A submission has been received."], [(user_id, f"Got it! Your phrase for **{acronym}** has been received.")]
    if g["phase"] == "voting":
        if low.startswith("/vote "):
            rest = content[6:].strip()
            try:
                n = int(rest)
            except ValueError:
                return True, ["Usage: /vote N (e.g. /vote 1)"], []
            if n < 1 or n > len(g["submissions"]):
                return True, [f"Vote 1–{len(g['submissions'])} only."], []
            g["votes"][user_id] = n - 1
            return True, [], []
        return True, [], []  # Ignore non-commands during voting
    # idle: allow normal chat or /start
    return False, [], []


def _record_win(room_id: int, user_id: int, username: str) -> None:
    """Persist win to DB."""
    try:
        db, AcroScore, _ = _get_db()
        row = AcroScore.query.filter_by(room_id=room_id, user_id=user_id).first()
        if row:
            row.wins += 1
        else:
            db.session.add(AcroScore(room_id=room_id, user_id=user_id, wins=1))
        db.session.commit()
    except Exception:
        pass  # Fallback: no-op if DB unavailable


def _get_score_replies(room_id: int) -> list[str]:
    """Return leaderboard for this room (wins). Persisted in DB."""
    try:
        db, AcroScore, User = _get_db()
        rows = AcroScore.query.filter_by(room_id=room_id).order_by(AcroScore.wins.desc()).limit(10).all()
        if not rows:
            return ["**Acrophobia scores** (this channel) — No wins yet. Play a round with /start!"]
        user_ids = [r.user_id for r in rows]
        users = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()}
        lines = ["**Acrophobia scores** (this channel):"]
        for i, row in enumerate(rows, 1):
            name = users.get(row.user_id) or f"User #{row.user_id}"
            lines.append(f"  **{i}.** {name}: {row.wins} win(s)")
        return ["\n".join(lines)]
    except Exception:
        return ["**Acrophobia scores** — Unable to load. Play a round with /start!"]


def _start_round(room_id: int) -> list[str]:
    g = _game(room_id)
    g["phase"] = "submitting"
    g["acronym"] = _random_acronym()
    g["submissions"] = []
    g["votes"] = {}
    g["end_time"] = time.time() + SUBMIT_SECONDS
    return [f"Round started! **Acronym: {g['acronym']}** – Reply with your phrase (one message) in {SUBMIT_SECONDS} seconds. Go!"]


def advance_submit_phase(room_id: int) -> list[str]:
    """Call when submit timer expires. Returns bot messages to send."""
    g = _game(room_id)
    if g["phase"] != "submitting":
        return []
    g["phase"] = "voting"
    g["end_time"] = time.time() + VOTE_SECONDS
    if not g["submissions"]:
        g["phase"] = "idle"
        return ["Time's up! No submissions. Type /start to play again."]
    lines = ["Time's up! **Vote for your favorite:**"]
    for i, s in enumerate(g["submissions"], 1):
        lines.append(f"  **{i}.** {s['phrase']}")
    lines.append(f"Reply with /vote N (1–{len(g['submissions'])}) in {VOTE_SECONDS} seconds.")
    return ["\n".join(lines)]


def advance_vote_phase(room_id: int) -> list[str]:
    """Call when vote timer expires. Returns bot messages to send."""
    g = _game(room_id)
    if g["phase"] != "voting":
        return []
    g["phase"] = "idle"
    if not g["votes"]:
        return ["No votes. Round over. Type /start to play again."]
    # Tally votes (by submission index)
    counts = {}
    for idx in g["votes"].values():
        counts[idx] = counts.get(idx, 0) + 1
    if not counts:
        return ["No valid votes. Type /start to play again."]
    winner_idx = max(counts, key=counts.get)
    winner = g["submissions"][winner_idx]
    _record_win(room_id, winner["user_id"], winner["username"])
    return [f"**Winner:** \"{winner['phrase']}\" by **{winner['username']}**! Congrats. Type /start for another round."]


def get_submit_end_time(room_id: int) -> float | None:
    """Return end time for submit phase (for timer). None if not in submit phase."""
    g = _game(room_id)
    if g["phase"] != "submitting":
        return None
    return g["end_time"]


def get_vote_end_time(room_id: int) -> float | None:
    g = _game(room_id)
    if g["phase"] != "voting":
        return None
    return g["end_time"]


def get_phase_info(room_id: int) -> dict:
    """Return current phase and end_time for the Acrophobia timer UI. end_time is Unix timestamp or None."""
    g = _game(room_id)
    phase = g["phase"]
    end_time = g["end_time"] if phase in ("submitting", "voting") else None
    return {"phase": phase, "end_time": end_time}
