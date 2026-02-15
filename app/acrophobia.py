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
        "**How to interact** — In this channel you can:",
        "  • Type **/help** or **/msg acrobot help** anytime for this message.",
        "  • Type **/start** or **/start X** (X=1–7) to start a new round or X consecutive rounds.",
        "  • During a round: reply with **one message** as your phrase for the acronym.",
        "  • During voting: type **/vote N** (e.g. /vote 1) to vote for submission N.",
        "",
        "**How to start a game** — Any user can type **/start** (single round) or **/start X** (X=1–7 consecutive rounds). The bot will post a 4- or 5-letter acronym; everyone has a short time to submit a phrase that fits (e.g. ABC → \"A Big Cat\"). Then everyone votes for their favorite; the winner is announced.",
        "",
        "**Rules** — (1) One phrase per person per round. (2) No editing after submit. (3) Vote once during the vote phase. (4) Have fun. Type **/score** for the leaderboard.",
    ]
    return ["\n".join(lines)]


def _acrobot_nickname() -> str:
    """Return a random nickname AcroBot uses for users (L'il Bro, L'il Homey, etc.)."""
    return random.choice(["L'il Bro", "L'il Homey"])


def _smack_talk() -> str:
    """Return a random smack talk line for between rounds."""
    return random.choice([
        "Don't get too comfortable.",
        "The crown is still up for grabs.",
        "Anyone can get lucky once.",
        "Let's see if you can back that up.",
        "Still a long way to go, champ.",
        "Don't count your chickens yet.",
    ])


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
            return True, ["This round is sudden death for the tied players only. Sit this one out."], []
        if any(s["user_id"] == user_id for s in g["submissions"]):
            return True, ["You already submitted this round."], []
        acronym = g["acronym"] or ""
        if not _phrase_matches_acronym(phrase, acronym):
            dm = f"Your phrase doesn't match the acronym **{acronym}**. Use a phrase whose first letter of each word spells that acronym."
            return True, [], [(user_id, dm)]
        g["submissions"].append({"user_id": user_id, "username": username, "phrase": phrase})
        nick = _acrobot_nickname()
        return True, ["A submission has been received."], [(user_id, f"Got it! Your phrase for **{acronym}** has been received, {nick}.")]

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
    if low == "/start" or (low.startswith("/start ") and low[7:].strip().isdigit()):
        if g["phase"] != "idle":
            return True, ["A round is already in progress. Wait for it to finish."], []
        g.pop("total_votes", None)  # Reset running tally for fresh game
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
            return True, ["This round is sudden death for the tied players only. Sit this one out."], []
        if any(s["user_id"] == user_id for s in g["submissions"]):
            return True, ["You already submitted this round."], []
        acronym = g["acronym"] or ""
        if not _phrase_matches_acronym(content, acronym):
            dm = f"Your phrase doesn't match the acronym **{acronym}**. Use a phrase whose first letter of each word spells that acronym."
            return True, [], [(user_id, dm)]
        g["submissions"].append({"user_id": user_id, "username": username, "phrase": content})
        nick = _acrobot_nickname()
        return True, ["A submission has been received."], [(user_id, f"Got it! Your phrase for **{acronym}** has been received, {nick}.")]
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
            nick = _acrobot_nickname()
            room_ack = [] if from_dm else ["A vote has been received."]
            dm_ack = [(user_id, f"Thanks. I got your vote for this round, {nick}.")]
            return True, room_ack, dm_ack
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


def _start_round(room_id: int, rounds: int = 1) -> list[str]:
    g = _game(room_id)
    g["phase"] = "submitting"
    g["acronym"] = _random_acronym()
    g["submissions"] = []
    g["votes"] = {}
    g["end_time"] = time.time() + SUBMIT_SECONDS
    g["rounds_remaining"] = max(1, min(7, rounds))
    rounds_msg = f" ({g['rounds_remaining']} round{'s' if g['rounds_remaining'] > 1 else ''})" if g["rounds_remaining"] > 1 else ""
    return [f"Round started!{rounds_msg} **Acronym: {g['acronym']}** – Reply with your phrase (one message) in {SUBMIT_SECONDS} seconds. Go!"]


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
        return ["Time's up! No submissions. Type /start to play again."], False
    replies = [f"Time's up! **Vote for your favorite.** Reply with /vote N (1–{len(g['submissions'])}) in {vote_sec} seconds."]
    for i, s in enumerate(g["submissions"], 1):
        replies.append(f"**{i}.** {s['phrase']}")
    return replies, sudden


def advance_vote_phase(room_id: int) -> tuple[list[str], bool, bool, dict | None]:
    """Call when vote timer expires. Returns (bot messages, start_next_round, is_sudden_death, winner_info)."""
    g = _game(room_id)
    if g["phase"] != "voting":
        return [], False, False, None
    if not g["votes"]:
        g["phase"] = "idle"
        return ["No votes. Round over. Type /start to play again."], False, False, None
    counts = {}
    for idx in g["votes"].values():
        counts[idx] = counts.get(idx, 0) + 1
    if not counts:
        g["phase"] = "idle"
        return ["No valid votes. Type /start to play again."], False, False, None
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
        return [f"**TIE!** Sudden death for {names}! **Acronym: {g['acronym']}** – {SUDDEN_DEATH_SUBMIT}s to submit. Go!"], True, True, None
    g["phase"] = "idle"
    g.pop("sudden_death", None)
    g.pop("sudden_death_players", None)
    winner_idx = tied_indices[0]
    winner = g["submissions"][winner_idx]
    _record_win(room_id, winner["user_id"], winner["username"])
    rounds_left = g.get("rounds_remaining", 1) - 1
    g["rounds_remaining"] = rounds_left

    # Full round results: submissions with vote counts
    replies = ["**Round results:**"]
    for i, s in enumerate(g["submissions"]):
        vc = counts.get(i, 0)
        replies.append(f"**{i + 1}.** \"{s['phrase']}\" by **{s['username']}** — {vc} vote{'s' if vc != 1 else ''}")

    # Update running total votes for multi-round games
    total_votes = g.setdefault("total_votes", {})
    for i, s in enumerate(g["submissions"]):
        uname = s["username"]
        total_votes[uname] = total_votes.get(uname, 0) + counts.get(i, 0)

    winner_msg = f"**Winner:** \"{winner['phrase']}\" by **{winner['username']}**! Fine, you got lucky on that one. Check ball."
    replies.append(winner_msg)
    winner_info = {"username": winner["username"], "user_id": winner["user_id"]}

    if rounds_left > 0:
        # Ongoing tally + smack talk between rounds
        tally_parts = [f"**{u}**: {v}" for u, v in sorted(total_votes.items(), key=lambda x: -x[1])]
        tally_msg = "**Total votes so far:** " + ", ".join(tally_parts) + "."
        replies.append(tally_msg)
        replies.append(_smack_talk())
        replies.append(f"{rounds_left} round(s) left. Next round starting…")
        return replies, True, False, winner_info
    replies[-1] += " Type /start for another round."
    return replies, False, False, winner_info


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
    """Return warning message for submit phase (30 or 15 seconds left). Adds urgency when <= 15 seconds."""
    if seconds_left <= 15:
        return f"**{seconds_left} seconds** left to submit your phrase! Hurry!"
    return f"**{seconds_left} seconds** left to submit your phrase!"


def get_vote_countdown_message(seconds_left: int) -> str:
    """Return countdown message for vote phase. Adds urgency when <= 15 seconds."""
    if seconds_left <= 15:
        return f"**{seconds_left} seconds** left to vote! Hurry!"
    return f"**{seconds_left} seconds** left to vote!"


def get_phase_info(room_id: int) -> dict:
    """Return current phase, end_time, and acronym for the Acrophobia timer UI. end_time is Unix timestamp or None."""
    g = _game(room_id)
    phase = g["phase"]
    end_time = g["end_time"] if phase in ("submitting", "voting") else None
    acronym = g.get("acronym") if phase == "submitting" else None
    return {"phase": phase, "end_time": end_time, "acronym": acronym}
