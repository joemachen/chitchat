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
    "Stupid sexy Flanders!",
    "Marge, get back here! He's going to give away our best table!",
    "You don't win friends with salad!",
    "Aw, 20 dollars? I wanted a peanut!",
    "Aww, twenty dollars? I wanted a peanut!",
    "Money can be exchanged for goods and services.",
    "Operator! Give me the number for 911!",
    "To alcohol! The cause of, and solution to, all of life's problems.",
    "I am so smart! S-M-R-T!",
    "I am so smart! S-M-R-T! I mean S-M-A-R-T!",
    "It's not easy to juggle a pregnant wife and a troubled child, but somehow I managed to fit in 8 hours of TV a day.",
    "Facts are meaningless. You could use facts to prove anything that's even remotely true!",
    "Kids, you tried your best and you failed miserably. The lesson is: never try.",
    "I'm not normally a praying man, but if you're up there, please save me, Superman!",
    "Beer. Now there's a temporary solution.",
    "I've learned that life is one crushing defeat after another until you just wish Flanders was dead.",
    "Lisa, if you don't like your job you don't strike. You just go in every day and do it really half-a**ed. That's the American way.",
    "Lisa, if you don't like your job you don't strike. You just go in every day and do it really halfway. That's the American way.",
    "Son, when you participate in sporting events, it's not whether you win or lose: it's how drunk you get.",
    "Oh, so they have internet on computers now!",
    "Oh, they have the Internet on computers now!",
    "I'm not a bad guy! I work hard, and I love my kids. So why should I spend half my Sunday hearing about how I'm going to Hell?",
    "Marge, it takes two to lie. One to lie and one to listen.",
    "I'm in no condition to drive. Wait, I don't have a license.",
    "I'm in no condition to drive... wait! I shouldn't listen to myself, I'm drunk!",
    "Shut up, brain, or I'll stab you with a Q-tip!",
    "I used to be with it, but then they changed what 'it' was. Now what I'm with isn't 'it' and what's 'it' seems weird and scary to me.",
    "All my life I've been an obese man trapped inside a fat man's body.",
    "Just because I don't care doesn't mean I don't understand.",
    "I'm not lazy, I'm just motivated to do nothing.",
    "Trying is the first step toward failure.",
    "Trying is the first step towards failure.",
    "If something's hard to do, then it's not worth doing.",
    "Let's all go out for some frosty chocolate milkshakes!",
    "I'm going to the back seat of my car, with the woman I love, and I won't be back for ten minutes!",
    "I want to share something with you: the three little sentences that will get you through life. Number 1: Cover for me. Number 2: Oh, good idea, Boss! Number 3: It was like that when I got here.",
    "Weaseling out of things is important to learn. It's what separates us from the animals... except the weasel.",
    "Television! Teacher, mother, secret lover.",
    # Additional quotes from homer_quotes.csv
    "The only monster here is the gambling monster that has enslaved your mother! I call him Gamblor!",
    "English? Who needs that? I'm never going to England.",
    "Maybe, just once, someone will call me 'Sir' without adding, 'You're making a scene.'",
    "Me fail English? That's unpossible.",
    "I have three kids and no money. Why can't I have no kids and three money?",
    "I think Smithers picked me because of my motivational skills. Everyone says they have to work a lot harder when I'm around.",
    "It's not a lie if you believe it.",
    "Simpson, Homer Simpson. He's the greatest guy in history. From the town of Springfield! He's about to hit a chestnut tree!",
    "Everything looks ten times better in the vacuum of space.",
    "The code of the schoolyard, Marge! The rules that teach a boy to be a man. Let's see. Don't tattle. Always make fun of those different from you. Never say anything unless you're sure everyone feels exactly the same way you do.",
    "Boring!",
    "And how is education supposed to make me feel smarter? Besides, every time I learn something new, it pushes some old stuff out of my brain. Remember when I took that home wine-making course, and I forgot how to drive?",
    "Mmm... forbidden donut.",
    "If he's so smart, how come he's dead?",
    "All my life I've had one dream: to achieve my many goals.",
    "Don't eat me. I have a wife and kids. Eat them!",
    "You'll have to speak up, I'm wearing a towel.",
    "Note to self: stop writing notes to self.",
    "But Marge, what if we chose the wrong religion? Each week we just make God madder and madder!",
    "Hehe! Look at him! He's going to eat that toaster!",
    "What's the point of going out? We're just gonna wind up back here anyway.",
    "The problem with your house, Flanders, is that you have the wrong number on the front. It should be 0.",
    "Can't talk, eating.",
    "To the Bee-mobile!",
    "Bart, with $10,000, we'd be millionaires! We could buy all kinds of useful things like... love!",
    "I'll make the supply run! I'll get the chips, dips, chains, and whips!",
    "I'm white-trash and I'm trouble! Okay, that's it!",
    "Mmm... organized crime.",
    "Marge, don't discourage the boy! Weaseling out of things is important to learn.",
    "I'm not a bad guy! I work hard, and I love my kids.",
    "Homer no function beer well without.",
    "Dear Lord, thank you for this microwave bounty.",
    "You tried your best and you failed miserably. The lesson is, never try.",
    "Bart, a woman is like a beer. They look good, they smell good...",
    "Marriage is like a coffin and each kid is another nail.",
    "I'm a white male, age 18 to 49. Everyone listens to me, no matter how dumb my suggestions are.",
    "If something's hard to do, then it's not worth doing. You just stick that guitar in the closet next to your short-wave radio.",
    "The answer to life's problems aren't at the bottom of a bottle, they're on TV!",
    "Mmm... 64 slices of American cheese.",
    "I'm not normally a praying man, but if you're up there, please save me, Superman!",
    "Son, a woman is like a beer. They look good, they smell good, and you'd step over your own mother just to get one!",
    "Oh, I have three kids and no money. Why can't I have no kids and three money?",
    "Marge, you're as pretty as Princess Leia and as smart as Yoda.",
    "I've done everything the Bible says — even the stuff that contradicts the other stuff!",
    "When will I learn? The answer to life's problems aren't at the bottom of a bottle... they're on TV!",
    "If God didn't want us to eat in church, he would have made gluttony a sin.",
    "It's like something out of that book, 'To Kill a Mockingbird.' I don't know, I never read it.",
    "Rock and roll had two good years: 1985 and 1990.",
    "Marge, I'm going to miss you so much. And it's not just the sex. It's also the food preparation.",
    "I've learned that life is one crushing defeat after another until you just wish Flanders was dead.",
    "I'm not lazy! I'm just... energy efficient.",
    "You know, boys, a nuclear reactor is a lot like a woman. You just have to read the manual and press the right buttons.",
    "Mmm... unexplained bacon.",
    "I want to be a good father. But every time I try, something good is on TV.",
    "In this house we obey the laws of thermodynamics!",
    "Marge, I agree with you — in theory. In theory, communism works. In theory.",
    "Homer Simpson does not lie twice on the same form.",
    "I'm not a bad guy. I just sometimes do bad things.",
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


# Homer-esque DM replies when users message him directly
HOMER_DM_REPLIES = [
    "Mmm... a message. *reads* D'oh! I mean, hey! What's up?",
    "Woo-hoo! Someone's talking to me! What do you need, friend?",
    "D'oh! You messaged me? I was just thinking about donuts. What's going on?",
    "Oh, hi there! Homer Simpson at your service. Need a quote? Try !Simpsons in a channel!",
    "Mmm... message. *scratches belly* Yeah, I'm here. What can I do for ya?",
    "Can't talk, eating. ...Okay, I'm done. What's up?",
    "You'll have to speak up, I'm wearing a towel. ...Metaphorically. What do you need?",
    "Mmm... forbidden donut. I mean, mmm... a DM! Hey!",
    "Note to self: someone messaged me. Better reply! Hi there!",
    "To alcohol! The cause of, and solution to, all of life's problems. Also, hey! You messaged me!",
    "What's the point of going out? We're just gonna wind up back here anyway. So... what's up?",
]


def get_homer_dm_reply() -> str:
    """Return a random Homer-esque reply for DMs."""
    return random.choice(HOMER_DM_REPLIES)
