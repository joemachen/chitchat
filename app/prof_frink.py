"""
Prof Frink trivia bot. Eccentric, cartoonish, nutty professor (Jerry Lewis style).
Responds only in the #Trivia channel. Fetches trivia from simpsons-trivia.com or placeholder.
"""
import random
from dataclasses import dataclass
from typing import Optional

# API placeholder: simpsons-trivia.com/api returns 404. Use static data until API is available.
# When API exists, fetch from: TRIVIA_API_URL (e.g. https://simpsons-trivia.com/api/questions)
TRIVIA_API_URL: Optional[str] = None  # Set in config when API is available

FRINKISMS = [
    "Glavin!",
    "Hoyvin!",
    "Flayvin!",
    "Glaaven!",
    "Shabooey!",
    "Glaaven-glaven!",
    "Ooh, the mathematics of it all!",
    "Yes, yes, the flux capacitor—I mean, the thingamajig!",
]

# Placeholder trivia: (question, answer, difficulty, season)
# Difficulty: beginner | intermediate | advanced | master
# When API is available, replace with fetch from TRIVIA_API_URL
PLACEHOLDER_TRIVIA = [
    ("In 'The Homer They Fall', who is Homer's manager for his boxing career?", "Moe", "intermediate", 8),
    ("In 'Blame It On Lisa', what is the first name of the Brazilian orphan boy Lisa sponsored?", "Ronaldo", "intermediate", 13),
    ("In 'The Wizard of Evergreen Terrace', what inventor does Homer idolize?", "Thomas Edison", "advanced", 10),
    ("In 'Krusty Gets Kancelled', who plays musical wine glasses on the Krusty Special?", "Hugh Hefner", "advanced", 4),
    ("In 'Separate Vocations', what career result does Bart get?", "Police officer", "intermediate", 3),
    ("In 'Treehouse of Horror IV', what drink does Mr. Burns serve that Homer mistakes for punch?", "Blood", "beginner", 5),
    ("In 'Marge Be Not Proud', what is Millhouse's character's INTENDED name in the video game?", "Thrillhouse", "advanced", 7),
    ("In 'Some Enchanted Evening', who lets the babysitter go free?", "Homer", "beginner", 1),
    ("In 'The Telltale Head', according to the church sign, what occurs on Tuesday nights?", "Bingo", "intermediate", 1),
    ("In 'Goo Goo Gai Pan', what country does Selma decide to adopt her baby from?", "China", "beginner", 16),
    ("What is the name of Moe's bar?", "Moe's Tavern", "beginner", None),
    ("Who is the principal of Springfield Elementary?", "Principal Skinner", "beginner", None),
    ("What is the name of the nuclear power plant where Homer works?", "Springfield Nuclear Power Plant", "beginner", None),
    ("What is Bart's catchphrase?", "Eat my shorts", "beginner", None),
    ("Who is Homer's next-door neighbor?", "Ned Flanders", "beginner", None),
]

_frink_active = True
_frink_daily_enabled = False
_frink_difficulty: Optional[str] = None  # beginner | intermediate | advanced | master
_frink_seasons: Optional[list[int]] = None  # e.g. [1, 2, 3] or None for all

# Active question per room_id: {"answer": str, "question_msg_id": int} — cleared when answered or timeout
_active_trivia: dict[int, dict] = {}

# Multi-round sessions: room_id -> rounds left to post after current (for !trivia X)
_trivia_rounds_remaining: dict[int, int] = {}

# Hot streaks: (room_id, user_id) -> consecutive correct count
_trivia_streak: dict[tuple[int, int], int] = {}

HOT_STREAK_PHRASES = [
    "Ooh, the mathematics of a hot streak! Glavin!",
    "Two in a row! The probability is most favorable!",
    "Three consecutive! The flux capacitor approves!",
    "Four! Four! Hoyvin-glaven!",
    "Five! A pentagon of perfection!",
    "Six! The hex of knowledge!",
    "Seven! A week of wisdom! Shabooey!",
]


@dataclass
class TriviaQuestion:
    """A single trivia question from the API or placeholder."""
    question: str
    answer: str
    difficulty: str
    season: Optional[int]


def _random_frinkism() -> str:
    """Return a random Frink exclamation."""
    return random.choice(FRINKISMS)


def _filter_by_difficulty(questions: list[tuple], difficulty: Optional[str]) -> list[tuple]:
    if not difficulty:
        return questions
    return [q for q in questions if q[2] == difficulty]


def _filter_by_seasons(questions: list[tuple], seasons: Optional[list[int]]) -> list[tuple]:
    if not seasons:
        return questions
    return [q for q in questions if q[3] is None or q[3] in seasons]


def fetch_trivia_question() -> Optional[TriviaQuestion]:
    """
    Fetch one random trivia question.
    Uses placeholder data until TRIVIA_API_URL is configured.
    TODO: When simpsons-trivia.com API is available, implement:
        response = requests.get(TRIVIA_API_URL, params={"difficulty": ..., "season": ...})
        return TriviaQuestion(**response.json())
    """
    questions = list(PLACEHOLDER_TRIVIA)
    questions = _filter_by_difficulty(questions, _frink_difficulty)
    questions = _filter_by_seasons(questions, _frink_seasons)
    if not questions:
        questions = list(PLACEHOLDER_TRIVIA)
    q = random.choice(questions)
    return TriviaQuestion(question=q[0], answer=q[1], difficulty=q[2], season=q[3])


def is_frink_active() -> bool:
    return _frink_active


def set_frink_active(active: bool) -> None:
    global _frink_active
    _frink_active = bool(active)


def is_frink_daily_enabled() -> bool:
    return _frink_daily_enabled


def set_frink_daily_enabled(enabled: bool) -> None:
    global _frink_daily_enabled
    _frink_daily_enabled = bool(enabled)


def get_frink_difficulty() -> Optional[str]:
    return _frink_difficulty


def set_frink_difficulty(difficulty: Optional[str]) -> None:
    global _frink_difficulty
    if difficulty in ("beginner", "intermediate", "advanced", "master", None):
        _frink_difficulty = difficulty


def get_frink_seasons() -> Optional[list[int]]:
    return _frink_seasons


def set_frink_seasons(seasons: Optional[list[int]]) -> None:
    global _frink_seasons
    if seasons is None:
        _frink_seasons = None
    else:
        _frink_seasons = [s for s in seasons if isinstance(s, int) and 1 <= s <= 20]


def get_frink_settings() -> dict:
    """Return current bot configuration for !settings display."""
    return {
        "active": _frink_active,
        "daily_enabled": _frink_daily_enabled,
        "difficulty": _frink_difficulty or "all",
        "seasons": _frink_seasons or "all",
    }


def format_frink_reply(text: str, include_frinkism: bool = True) -> str:
    """Wrap a reply with optional Frink flair."""
    if include_frinkism and random.random() < 0.4:
        prefix = f"{_random_frinkism()} "
    else:
        prefix = ""
    return f"{prefix}{text}"


def get_frink_dm_reply() -> str:
    """Return a random Frink-y reply for DMs."""
    dm_replies = [
        "Glavin! The flux capacitor is buzzing! What can this humble scientist do for you?",
        "Hoyvin! A message! Ooh, the mathematics of communication!",
        "Yes, yes! You've reached the lab. The thingamajig is at your service!",
        "Shabooey! Prof Frink here, ready to assist with all matters scientific!",
        "Glaaven! Your message has been received. The probability of a reply is 100%!",
    ]
    return random.choice(dm_replies)


def get_trivia_response() -> tuple[str, str]:
    """
    Fetch a trivia question and return (question_message, answer_for_later).
    The question is posted; the answer is revealed when first correct chat message or after timeout.
    """
    tq = fetch_trivia_question()
    if not tq:
        return format_frink_reply("The trivia flux capacitor is on the fritz! Try again later, glavin!"), ""
    msg = format_frink_reply(f"**Trivia time!** {tq.question}")
    return msg, tq.answer


def set_active_trivia(room_id: int, answer: str, question_msg_id: int) -> None:
    """Record active question for answer matching."""
    global _active_trivia
    _active_trivia[room_id] = {"answer": answer, "question_msg_id": question_msg_id}


def get_active_trivia(room_id: int) -> Optional[dict]:
    """Get active question for room, or None."""
    return _active_trivia.get(room_id)


def clear_active_trivia(room_id: int) -> None:
    """Clear active question (answered or timeout)."""
    global _active_trivia
    _active_trivia.pop(room_id, None)


def get_trivia_rounds_remaining(room_id: int) -> int:
    """Rounds left to post after current (for !trivia X)."""
    return _trivia_rounds_remaining.get(room_id, 0)


def set_trivia_rounds_remaining(room_id: int, n: int) -> None:
    """Set rounds left for multi-round session."""
    global _trivia_rounds_remaining
    if n <= 0:
        _trivia_rounds_remaining.pop(room_id, None)
    else:
        _trivia_rounds_remaining[room_id] = n


def _normalize(s: str) -> str:
    """Normalize for comparison: lower, strip, collapse whitespace, remove apostrophes."""
    return " ".join(s.strip().lower().replace("'", "").split())


def check_trivia_answer(room_id: int, user_answer: str) -> Optional[str]:
    """
    If user_answer matches the active question (case-insensitive), return the canonical answer and clear.
    Otherwise return None.
    """
    active = get_active_trivia(room_id)
    if not active:
        return None
    if _normalize(user_answer) == _normalize(active["answer"]):
        canonical = active["answer"]
        clear_active_trivia(room_id)
        return canonical
    return None


def get_trivia_leaderboard(room_id: int, limit: int = 10) -> list[tuple[str, int]]:
    """Return list of (username, correct_count) for room, sorted by correct desc."""
    from app.models import TriviaScore, User
    rows = (
        TriviaScore.query.filter_by(room_id=room_id)
        .order_by(TriviaScore.correct.desc())
        .limit(limit)
        .all()
    )
    result = []
    for row in rows:
        u = User.query.get(row.user_id)
        name = u.username if u else f"User#{row.user_id}"
        result.append((name, row.correct))
    return result


def _reset_other_streaks(room_id: int, keep_user_id: int) -> None:
    """Reset streaks for everyone in room except keep_user_id."""
    global _trivia_streak
    to_remove = [k for k in _trivia_streak if k[0] == room_id and k[1] != keep_user_id]
    for k in to_remove:
        del _trivia_streak[k]


def clear_all_trivia_streaks(room_id: int) -> None:
    """Clear all streaks in room (e.g. on timeout with no winner)."""
    global _trivia_streak
    to_remove = [k for k in _trivia_streak if k[0] == room_id]
    for k in to_remove:
        del _trivia_streak[k]


def get_hot_streak_message(room_id: int, user_id: int) -> Optional[str]:
    """Return Frink-y message if user has hot streak (2+ consecutive correct), else None."""
    streak = _trivia_streak.get((room_id, user_id), 0)
    if streak >= 2 and streak <= 7:
        idx = min(streak - 2, len(HOT_STREAK_PHRASES) - 1)
        return HOT_STREAK_PHRASES[idx]
    if streak >= 8:
        return random.choice(HOT_STREAK_PHRASES) + f" {streak} in a row!"
    return None


def award_trivia_point(room_id: int, user_id: int) -> tuple[int, Optional[str]]:
    """Increment correct count for user in room. Returns (new_total, hot_streak_message)."""
    from app.models import TriviaScore, db
    global _trivia_streak
    _reset_other_streaks(room_id, user_id)
    _trivia_streak[(room_id, user_id)] = _trivia_streak.get((room_id, user_id), 0) + 1
    streak_msg = get_hot_streak_message(room_id, user_id)

    row = TriviaScore.query.filter_by(room_id=room_id, user_id=user_id).first()
    if row:
        row.correct = (row.correct or 0) + 1
    else:
        row = TriviaScore(room_id=room_id, user_id=user_id, correct=1)
        db.session.add(row)
    db.session.commit()
    return row.correct, streak_msg


def get_help_text() -> str:
    """Frink-flavored help menu."""
    return "\n".join([
        "**Prof Frink — Trivia Bot** " + _random_frinkism(),
        "",
        "**Commands** (only in #Trivia channel):",
        "• **!trivia** or **!trivia X** (X=1–7) — Fetch one or X consecutive Simpsons trivia questions (first correct answer wins a point)",
        "• **!daily** — Toggle daily automated trivia post (admin or frink_control)",
        "• **!set-difficulty [beginner|intermediate|advanced|master]** — Filter by difficulty",
        "• **!set-seasons [1-20]** — Filter by season(s), e.g. !set-seasons 1 2 3",
        "• **!settings** — Show current bot configuration",
        "• **!score** / **/score** — Show trivia leaderboard",
        "• **!help** / **!commands** — This message",
        "",
        "The mathematics of knowledge await! Hoyvin-glaven!",
    ])
