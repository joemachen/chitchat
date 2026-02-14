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


def _random_acronym(length: int | None = None, sudden_death: bool = False) -> str:
    """Return a random acronym. Default 4-5 letters; sudden_death uses 3-4 letters."""
    if sudden_death:
        if length not in (3, 4):
            length = random.choice((3, 4))
    elif length not in (4, 5):
        length = random.choice((4, 5))
    return "".join(random.choices(string.ascii_uppercase, k=length))

# Game state per room_id: phase, acronym, submissions, votes, end_time, rounds_remaining
_games = {}

# Super Admins can activate/deactivate the bot in Settings
_acrobot_active = True

SUBMIT_SECONDS = 60
VOTE_SECONDS = 45
SUDDEN_DEATH_SUBMIT = 30
SUDDEN_DEATH_VOTE = 30


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
            "rounds_remaining": 1,  # for /start X
        }
    return _games[room_id]


def _get_help_replies() -> list[str]:
    """Full help text for AcroBot: how to interact, start a game, rules. Returns one message."""
    lines = [
        "**AcroBot — Acrophobia** (acronym phrase game)",
        "",
        "Yo, The Glove in the building. Here's the playbook:",
        "  • **/help** or **/msg acrobot help** — this message.",
        "  • **/start** or **/start X** (X=1–7) — start a round or X rounds.",
        "  • During a round: drop **one message** as your phrase for the acronym.",
        "  • During voting: **/vote N** (e.g. /vote 1) — pick your favorite.",
        "",
        "**How it works** — /start kicks it off. I post a 4- or 5-letter acronym; y'all got time to submit a phrase that fits (e.g. ABC → \"A Big Cat\"). Then vote. Winner gets the W.",
        "",
        "**Rules** — One phrase per person. No editing. Vote once. And don't choke. **/score** for the leaderboard.",
    ]
    return ["\n".join(lines)]


def _phrase_matches_acronym(phrase: str, acronym: str) -> bool:
    """True if the phrase's first letter of each word (case-insensitive) spells the acronym."""
    if not phrase or not acronym:
        return False
    words = phrase.strip().split()
    letters = "".join(w[0] for w in words if w).upper()
    return letters == acronym.upper()


def handle_message(room_id: int, user_id: int, username: str, content: str, from_dm: bool = False) -> tuple[bool, list[str], list[tuple[int, str]]]:
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
        sudden_players = g.get("sudden_death_players")
        if sudden_players and user_id not in sudden_players:
            return True, ["Sudden death is for the tied players only. Y'all sit this one out."], []
        if any(s["user_id"] == user_id for s in g["submissions"]):
            return True, ["You already dropped one. Don't double-dribble."], []
        acronym = g["acronym"] or ""
        if not _phrase_matches_acronym(phrase, acronym):
            dm = f"That's not even close! **{acronym}** — first letter of each word spells it. You know the rules. Try again before the clock runs out."
            return True, [], [(user_id, dm)]
        g["submissions"].append({"user_id": user_id, "username": username, "phrase": phrase})
        return True, ["Someone got one in. Let's see if the rest of y'all can keep up."], [(user_id, "Locked in. Don't choke now.")]

    # /m, /msg, /message acrobot <anything> or !acrobot <anything> — generic reply when not a submission
    if _acrobot_prefix:
        rest = low.split("acrobot", 1)[-1].strip()
        if rest != "help":
            if _acrobot_active:
                return True, ["Yo, AcroBot in the building. **/help** or **/msg acrobot help** if you need the playbook."], []
            return True, ["AcroBot is currently offline. A Super Admin can activate me in Settings."], []

    # When bot is offline: only respond to game-related input with offline message; /score still works
    if not _acrobot_active:
        if low == "/score":
            return True, _get_score_replies(room_id), []
        if low == "/start" or low.startswith("/vote ") or g["phase"] != "idle":
            return True, ["AcroBot is currently offline. A Super Admin can activate me in Settings."], []
        return False, [], []

    # Commands
    if low == "/start" or (low.startswith("/start ") and low[7:].strip().isdigit()):
        if g["phase"] != "idle":
            return True, ["We already got a game going. Chill."], []
        rounds = 1
        if low.startswith("/start "):
            try:
                r = int(low[7:].strip())
                rounds = max(1, min(7, r))
            except ValueError:
                pass
        return True, _start_round(room_id, rounds=rounds), []
    if low == "/score":
        return True, _get_score_replies(room_id), []

    if g["phase"] == "submitting":
        if low.startswith("/"):
            return True, [], []
        sudden_players = g.get("sudden_death_players")
        if sudden_players and user_id not in sudden_players:
            return True, ["Sudden death is for the tied players only. Y'all sit this one out."], []
        if any(s["user_id"] == user_id for s in g["submissions"]):
            return True, ["You already dropped one. Don't double-dribble."], []
        acronym = g["acronym"] or ""
        if not _phrase_matches_acronym(content, acronym):
            dm = f"That's not even close! **{acronym}** — first letter of each word spells it. You know the rules. Try again before the clock runs out."
            return True, [], [(user_id, dm)]
        g["submissions"].append({"user_id": user_id, "username": username, "phrase": content})
        return True, ["Someone got one in. Let's see if the rest of y'all can keep up."], [(user_id, "Locked in. Don't choke now.")]
    if g["phase"] == "voting":
        if low.startswith("/vote "):
            rest = content[6:].strip()
            try:
                n = int(rest)
            except ValueError:
                return True, ["Pick a number. /vote N. Like /vote 1. Simple."], []
            if n < 1 or n > len(g["submissions"]):
                return True, [f"Pick 1 through {len(g['submissions'])}. That's the range."], []
            g["votes"][user_id] = n - 1
            dm_ack = [(user_id, "Vote recorded. Don't let me down.")] if from_dm else []
            return True, [], dm_ack
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
            return ["**Acrophobia scores** (this channel) — No wins yet. Soft. Play a round with /start!"]
        user_ids = [r.user_id for r in rows]
        users = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()}
        lines = ["**Acrophobia scores** (this channel):"]
        for i, row in enumerate(rows, 1):
            name = users.get(row.user_id) or f"User #{row.user_id}"
            lines.append(f"  **{i}.** {name}: {row.wins} win(s)")
        return ["\n".join(lines)]
    except Exception:
        return ["**Acrophobia scores** — Unable to load. Play a round with /start!"]


def _start_round(room_id: int, rounds: int = 1) -> list[str]:
    g = _game(room_id)
    g["phase"] = "submitting"
    g["acronym"] = _random_acronym()
    g["submissions"] = []
    g["votes"] = {}
    g["end_time"] = time.time() + SUBMIT_SECONDS
    g["rounds_remaining"] = max(1, min(7, rounds))
    rounds_msg = f" ({g['rounds_remaining']} round{'s' if g['rounds_remaining'] > 1 else ''})" if g["rounds_remaining"] > 1 else ""
    return [f"Alright, check it.{rounds_msg} **Acronym: {g['acronym']}** — {SUBMIT_SECONDS} seconds. Don't go out like a scrub. Get your phrase in. Go!"]


def advance_submit_phase(room_id: int) -> tuple[list[str], bool]:
    """Call when submit timer expires. Returns (bot messages, is_sudden_death)."""
    g = _game(room_id)
    if g["phase"] != "submitting":
        return [], False
    sudden = g.get("sudden_death", False)
    vote_sec = SUDDEN_DEATH_VOTE if sudden else VOTE_SECONDS
    g["phase"] = "voting"
    g["end_time"] = time.time() + vote_sec
    if not g["submissions"]:
        g["phase"] = "idle"
        g.pop("sudden_death", None)
        g.pop("sudden_death_players", None)
        return ["Clock ran out! Nobody showed up? Soft. Type /start when y'all ready to play for real."], False
    replies = [f"Time's up! Pick your favorite. /vote N (1–{len(g['submissions'])}) — {vote_sec} seconds. Don't leave me hanging."]
    for i, s in enumerate(g["submissions"], 1):
        replies.append(f"**{i}.** {s['phrase']}")
    return replies, sudden


def advance_vote_phase(room_id: int) -> tuple[list[str], bool, bool]:
    """Call when vote timer expires. Returns (bot messages, start_next_round, is_sudden_death)."""
    g = _game(room_id)
    if g["phase"] != "voting":
        return [], False, False
    if not g["votes"]:
        g["phase"] = "idle"
        return ["Nobody voted? Y'all scared to pick a winner? /start when you're ready."], False, False
    counts = {}
    for idx in g["votes"].values():
        counts[idx] = counts.get(idx, 0) + 1
    if not counts:
        g["phase"] = "idle"
        return ["Nobody voted? Y'all scared to pick a winner? /start when you're ready."], False, False
    max_votes = max(counts.values())
    tied_indices = [idx for idx, c in counts.items() if c == max_votes]
    if len(tied_indices) > 1:
        tied_user_ids = {g["submissions"][idx]["user_id"] for idx in tied_indices}
        tied_usernames = [g["submissions"][idx]["username"] for idx in tied_indices]
        g["phase"] = "submitting"
        g["sudden_death"] = True
        g["sudden_death_players"] = tied_user_ids
        g["acronym"] = _random_acronym(sudden_death=True)
        g["submissions"] = []
        g["votes"] = {}
        g["end_time"] = time.time() + SUDDEN_DEATH_SUBMIT
        names = ", ".join(tied_usernames)
        return [f"**TIE!** Sudden death for {names}! **Acronym: {g['acronym']}** — {SUDDEN_DEATH_SUBMIT}s to submit. One of you gonna step up. Go!"], True, True
    g["phase"] = "idle"
    g.pop("sudden_death", None)
    g.pop("sudden_death_players", None)
    winner_idx = tied_indices[0]
    winner = g["submissions"][winner_idx]
    _record_win(room_id, winner["user_id"], winner["username"])
    rounds_left = g.get("rounds_remaining", 1) - 1
    g["rounds_remaining"] = rounds_left
    msg = f"**Winner:** \"{winner['phrase']}\" by **{winner['username']}**! Fine, you got lucky on that one. Check ball."
    if rounds_left > 0:
        return [msg + f" {rounds_left} round(s) left. Next round starting…"], True, False
    return [msg + " Type /start for another round."], False, False


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


def get_submit_warning_message(seconds_left: int) -> str:
    """Return warning message for submit phase (30 or 15 seconds left)."""
    return f"**{seconds_left} seconds** left! The clock is ticking, don't go out like a scrub!"


def get_vote_countdown_message(seconds_left: int) -> str:
    """Return countdown message for vote phase (10 seconds left)."""
    return f"**{seconds_left} seconds** to vote! Pick one or sit down."


def get_phase_info(room_id: int) -> dict:
    """Return current phase, end_time, and acronym for the Acrophobia timer UI. end_time is Unix timestamp or None."""
    g = _game(room_id)
    phase = g["phase"]
    end_time = g["end_time"] if phase in ("submitting", "voting") else None
    acronym = g.get("acronym") if phase == "submitting" else None
    return {"phase": phase, "end_time": end_time, "acronym": acronym}
