"""
Homer bot: responds to !Simpsons with random Simpsons quotes.
Online/offline toggle in Settings (like AcroBot).
"""
import random

# Simpsons quotes (mostly Homer, some iconic show quotes)
SIMPSONS_QUOTES = [
    "D'oh!",
    "Mmm... donuts.",
    "Woo-hoo!",
    "Why you little...!",
    "Stupid Flanders!",
    "Marge, get back here! He's going to give away our best table!",
    "You don't win friends with salad!",
    "Aw, 20 dollars? I wanted a peanut!",
    "Money can be exchanged for goods and services.",
    "Operator! Give me the number for 911!",
    "To alcohol! The cause of, and solution to, all of life's problems.",
    "I am so smart! S-M-R-T!",
    "It's not easy to juggle a pregnant wife and a troubled child, but somehow I managed to fit in 8 hours of TV a day.",
    "Facts are meaningless. You could use facts to prove anything that's even remotely true!",
    "Kids, you tried your best and you failed miserably. The lesson is: never try.",
    "I'm not normally a praying man, but if you're up there, please save me, Superman!",
    "Beer. Now there's a temporary solution.",
    "I've learned that life is one crushing defeat after another until you just wish Flanders was dead.",
    "Lisa, if you don't like your job you don't strike. You just go in every day and do it really half-a**ed. That's the American way.",
    "Son, when you participate in sporting events, it's not whether you win or lose: it's how drunk you get.",
    "Oh, so they have internet on computers now!",
    "I'm not a bad guy! I work hard, and I love my kids. So why should I spend half my Sunday hearing about how I'm going to Hell?",
    "Marge, it takes two to lie. One to lie and one to listen.",
    "I'm in no condition to drive. Wait, I don't have a license.",
    "Shut up, brain, or I'll stab you with a Q-tip!",
    "I used to be with it, but then they changed what 'it' was. Now what I'm with isn't 'it' and what's 'it' seems weird and scary to me.",
    "All my life I've been an obese man trapped inside a fat man's body.",
    "Just because I don't care doesn't mean I don't understand.",
    "I'm not lazy, I'm just motivated to do nothing.",
    "Trying is the first step toward failure.",
    "If something's hard to do, then it's not worth doing.",
    "Let's all go out for some frosty chocolate milkshakes!",
    "I'm going to the back seat of my car, with the woman I love, and I won't be back for ten minutes!",
    "I want to share something with you: the three little sentences that will get you through life. Number 1: Cover for me. Number 2: Oh, good idea, Boss! Number 3: It was like that when I got here.",
    "Weaseling out of things is important to learn. It's what separates us from the animals... except the weasel.",
    "Television! Teacher, mother, secret lover.",
    "I am so smart! S-M-R-T! I mean S-M-A-R-T!",
]

_homer_active = True


def is_homer_active() -> bool:
    return _homer_active


def set_homer_active(active: bool) -> None:
    global _homer_active
    _homer_active = bool(active)


def get_random_simpsons_quote() -> str:
    """Return a random Simpsons quote."""
    return random.choice(SIMPSONS_QUOTES)
