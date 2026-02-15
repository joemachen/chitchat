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


def get_trivia_response() -> tuple[str, str]:
    """
    Fetch a trivia question and return (question_message, answer_for_later).
    The question is posted; the answer can be revealed after a delay or on command.
    """
    tq = fetch_trivia_question()
    if not tq:
        return format_frink_reply("The trivia flux capacitor is on the fritz! Try again later, glavin!"), ""
    msg = format_frink_reply(f"**Trivia time!** {tq.question}")
    return msg, tq.answer


def get_help_text() -> str:
    """Frink-flavored help menu."""
    return "\n".join([
        "**Prof Frink — Trivia Bot** " + _random_frinkism(),
        "",
        "**Commands** (only in #Trivia channel):",
        "• **!trivia** — Fetch one random Simpsons trivia question",
        "• **!daily** — Toggle daily automated trivia post (Surfer Girl or frink_control)",
        "• **!set-difficulty [beginner|intermediate|advanced|master]** — Filter by difficulty",
        "• **!set-seasons [1-20]** — Filter by season(s), e.g. !set-seasons 1 2 3",
        "• **!settings** — Show current bot configuration",
        "• **!help** / **!commands** — This message",
        "",
        "The mathematics of knowledge await! Hoyvin-glaven!",
    ])
