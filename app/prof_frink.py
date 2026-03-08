"""
Prof Frink trivia bot. Eccentric, cartoonish, nutty professor (Jerry Lewis style).
Responds only in the #Trivia channel. Fetches trivia from simpsons-trivia.com or placeholder.
"""
import random
import time

TRIVIA_SECONDS = 45  # Time limit to answer each question
from dataclasses import dataclass
from typing import Optional

# API placeholder: simpsons-trivia.com/api returns 404. Use static data until API is available.
# When API exists, fetch from: TRIVIA_API_URL (e.g. https://simpsons-trivia.com/api/questions)
TRIVIA_API_URL: Optional[str] = None  # Set in config when API is available

FRINKISMS = [
    "Glavin!",
    "Glaven!",
    "Hoyvin!",
    "Hoyvin-mayvin!",
    "Flavin!",
    "Flayvin!",
    "Glaaven!",
    "Shabooey!",
    "Glaaven-glaven!",
    "Ooh, the mathematics of it all!",
    "Yes, yes, the flux capacitor—I mean, the thingamajig!",
    "Hoyvin-glaven!",
    "The probability is most favorable!",
    "Eureka! Well, almost eureka!",
    "By Jove—I mean, by science!",
    "The cosmic ballet goes on!",
    "Fascinating! Absolutely fascinating!",
    "The thingamajig is operational!",
    "Ooh, the flux capacitor approves!",
    "Shabooey-shabooey!",
    "The mathematics never lie!",
    "A most scientific occurrence!",
]

# Longer Frink quotes from the show — used in DMs, ridicule, hot streaks
FRINK_QUOTES = [
    "With the running and the jumping and the hitting and the pain!",
    '"Glavin, out!"',
    '"Oh, the biting and the scratching and the hair-pulling! Oh, I\'m in such pain!"',
    "With the shouting and the shoving and the hoo-ha!",
    "Pi is exactly three!",
    '"Good morning, ma\'am. Good morning, sir. Good morning, thing."',
    '"I\'ve predicted that within ten years, computers will be twice as powerful, ten thousand times larger, and so expensive that only the five richest kings of Europe will own them."',
    '"This is the Frinkometer! It measures the gaseous emissions of the... oh, it\'s just a glorified sneeze-detector."',
    '"I\'ve invented a machine that can actually extract the essence of a person\'s soul! Unfortunately, it looks exactly like a waffle iron."',
    '"Behold! The Debulking Ray! It will turn this giant donut into a tiny, digestible pill!"',
    '"This is my Laughter-Induced-Death Ray! It\'s not finished yet, but it\'s already quite ticklish."',
    '"Behold the Hover-Bike! It stays three inches off the ground, unless you weigh more than a squirrel."',
    '"I\'ve created a Sarcasm Detector. Oh, that\'s a real useful invention!"',
    '"The Matter Transporter! It\'s 99% safe! But that 1%... oh, the horror. The teleporting horror!"',
    "I've designed this Electronic Marriage Counselor. It uses logic to determine who is wrong. See? Science!",
    '"Behold! A ray that turns people into... well, smaller people!"',
    '"This is my Gamma-Ray Tanning Bed! It gives you a deep, healthy glow, and a third ear for better hearing!"',
    '"The Automatic Dog-Walker! It never gets tired, though it does occasionally try to bury the dog."',
    '"He\'s gone into... the Third Dimension! It\'s a world where things have length, width, and even depth!"',
    "It's like he's reached into the very fabric of reality and pulled out a... a... glaven!",
    '"I\'ll just use this shrink ray to go inside Homer\'s stomach. It\'s a dark, moist, donut-filled wonderland!"',
    '"I must warn you, the re-animation process can lead to some mild side effects, like an insatiable hunger for brains and a slight limp."',
    '"I\'ve invented a way to look into the future! It turns out we all die. Oops, spoilers!"',
    '"According to my calculations, the comet will collide with Springfield with the force of a billion billion... oh, let\'s just say it\'ll be a big boom."',
    '"The fireball is headed straight for us! Quickly, everyone into the Lead-Lined Bunker! No, wait, that\'s just a cardboard box with gray paint."',
    '"It\'s elementary physics, really. If you increase the velocity, you increase the hoo-ha!"',
    '"I\'m sorry, I can\'t hear you over the sound of my own genius!"',
    '"You see, the liquid nitrogen freezes the molecules, causing a state of... oh, look at the pretty blue ice!"',
    "The wobbling is caused by the gravitational pull of the... thingy.",
    "I've discovered a new element! I call it Frinkium. It's highly unstable and smells like burnt toast.",
    '"My data shows that if we don\'t act now, the town will be underwater by Tuesday. Or maybe Wednesday. My watch is a bit slow."',
    '"If we hit the \'Enter\' key, we will either save the world or blow up the local laundromat."',
    '"I\'m a lonely man, but I have my robots! They don\'t love me, but they do make excellent toast."',
    "I was just... uh... testing the structural integrity of this locker. From the inside.",
    '"I have a date! A real, live human date! I must calculate the optimal amount of eye contact."',
    "Why won't people listen to my warnings? Is it the glasses? The bow tie? The way I say 'glaven'?",
    "I'm not a dork! I'm a highly sophisticated intellectual with a specialized vocabulary!",
    '"Oh, I\'ve spilled my chemicals! Now I\'ll have to start my 20-year experiment all over again. Glavin."',
    '"I\'ve calculated that my chances of getting a second date are exactly... zero point zero zero... oh, dear."',
    '"I\'m not crying, my eyes are just leaking saline solution due to a localized emotional disturbance."',
    '"I\'ve discovered that the secret to eternal life is... oh, wait, I forgot to carry the one."',
    '"The monster is attacking! Quickly, hand me my Anti-Monster Spray! No, that\'s hairspray! Now he looks fabulous, but he\'s still biting!"',
    "Science is like a beautiful woman. Except she's made of numbers and doesn't reject me as much.",
    '"I\'ve analyzed the DNA, and it turns out the killer is... a bear? No, wait, it\'s a very hairy man."',
    "Don't touch that! It's a Prototype Death-Ray! Or a very powerful flashlight. I forget which.",
    '"I\'m working on a way to turn lead into gold, but so far I\'ve only turned gold into slightly cheaper gold."',
    '"The laws of physics do not apply to me! Well, except for gravity. That one is quite insistent."',
    "Everything is under control! Except for the screaming and the fire!",
]

# Simpsons trivia: (question, answer, difficulty, season)
# Difficulty: beginner | intermediate | advanced | master
# Season: 1-20 or None for general knowledge
PLACEHOLDER_TRIVIA = [
    # Beginner — general knowledge
    ("What is the name of Moe's bar?", "Moe's Tavern", "beginner", None),
    ("Who is the principal of Springfield Elementary?", "Principal Skinner", "beginner", None),
    ("What is the name of the nuclear power plant where Homer works?", "Springfield Nuclear Power Plant", "beginner", None),
    ("What is Bart's catchphrase?", "Eat my shorts", "beginner", None),
    ("Who is Homer's next-door neighbor?", "Ned Flanders", "beginner", None),
    ("What is Lisa's instrument?", "Saxophone", "beginner", None),
    ("What is Maggie's first word?", "Daddy", "beginner", None),
    ("Who owns the Kwik-E-Mart?", "Apu", "beginner", None),
    ("What is Mr. Burns's first name?", "Charles", "beginner", None),
    ("What does Homer say when he makes a mistake?", "D'oh", "beginner", None),
    ("Who is Bart's best friend?", "Milhouse", "beginner", None),
    ("What is the name of the Simpson family dog?", "Santa's Little Helper", "beginner", None),
    ("What is Marge's hair color?", "Blue", "beginner", None),
    ("Who is the family cat?", "Snowball", "beginner", None),
    ("What town do the Simpsons live in?", "Springfield", "beginner", None),
    ("What is Krusty's full stage name?", "Krusty the Clown", "beginner", None),
    ("Who is the school bully?", "Nelson", "beginner", None),
    ("What does Homer work as?", "Nuclear safety inspector", "beginner", None),
    ("Who is Bart's teacher?", "Edna Krabappel", "beginner", None),
    ("What is the name of the comic book store owner?", "Comic Book Guy", "beginner", None),
    # Beginner — by season
    ("In 'Some Enchanted Evening', who lets the babysitter go free?", "Homer", "beginner", 1),
    ("In 'Treehouse of Horror IV', what drink does Mr. Burns serve that Homer mistakes for punch?", "Blood", "beginner", 5),
    ("In 'Goo Goo Gai Pan', what country does Selma decide to adopt her baby from?", "China", "beginner", 16),
    ("In 'Bart the General', what does Bart organize to fight Nelson?", "Army", "beginner", 1),
    ("In 'Life on the Fast Lane', what does Marge receive for her birthday?", "Bowling ball", "beginner", 1),
    ("In 'Moaning Lisa', what game does Bart play with Lisa?", "Boxing", "beginner", 1),
    ("In 'The Crepes of Wrath', what country does Bart get sent to?", "Albania", "beginner", 1),
    ("In 'Krusty Gets Busted', who is framed for robbing the Kwik-E-Mart?", "Krusty", "beginner", 1),
    ("In 'Bart the Daredevil', what does Bart jump over on his skateboard?", "Springfield Gorge", "beginner", 2),
    ("In 'Itchy and Scratchy and Marge', what does Marge protest?", "Violence on TV", "beginner", 2),
    ("In 'Bart Gets Hit by a Car', who does the family sue?", "Mr. Burns", "beginner", 2),
    ("In 'Treehouse of Horror II', what does Homer sell his soul for?", "Donut", "beginner", 2),
    ("In 'Lisa's Substitute', who substitutes for Bart's teacher?", "Mr. Bergstrom", "beginner", 2),
    ("In 'War of the Simpsons', where do Homer and Marge go for marriage counseling?", "Catfish Lake", "beginner", 2),
    ("In 'Three Men and a Comic Book', what do the boys buy together?", "Radioactive Man", "beginner", 2),
    ("In 'Lisa's Pony', what does Homer get Lisa to stop her from crying?", "Pony", "beginner", 3),
    ("In 'Colonel Homer', what does Homer discover in a small town?", "Lurleen Lumpkin", "beginner", 3),
    ("In 'Black Widower', who does Selma marry?", "Sideshow Bob", "beginner", 3),
    ("In 'The Front', who writes for Itchy and Scratchy?", "Bart and Lisa", "beginner", 4),
    ("In 'Whacking Day', what do Springfielders traditionally whack?", "Snakes", "beginner", 4),
    ("In 'Marge vs. the Monorail', what does Lyle Lanley sell Springfield?", "Monorail", "beginner", 4),
    ("In 'Selma's Choice', what does Selma consider before having a baby?", "Duff Gardens", "beginner", 4),
    ("In 'Brother from the Same Planet', who does Bart get as a Big Brother?", "Tom", "beginner", 4),
    ("In 'I Love Lisa', what does Ralph give Lisa for Valentine's?", "Card", "beginner", 4),
    ("In 'Duffless', what does Homer give up for a month?", "Beer", "beginner", 4),
    ("In 'Last Exit to Springfield', what does Mr. Burns want to eliminate?", "Dental plan", "beginner", 4),
    ("In 'So It's Come to This', what does Bart say on the April Fool's prank?", "I'm dead", "beginner", 4),
    ("In 'The Boy Who Knew Too Much', who does Bart protect by not snitching?", "Freddy", "beginner", 5),
    ("In 'Treehouse of Horror V', what dimension do the family get trapped in?", "Third", "beginner", 6),
    ("In 'Bart's Girlfriend', who does Bart have a crush on?", "Jessica", "beginner", 6),
    ("In 'Lisa on Ice', what sport do Bart and Lisa compete in?", "Hockey", "beginner", 6),
    ("In 'Homer Badman', what does Homer accidentally steal?", "Gum", "beginner", 6),
    ("In 'Grampa vs. Sexual Inadequacy', what does Grampa sell?", "Tonic", "beginner", 6),
    ("In 'Fear of Flying', what is Marge afraid of?", "Flying", "beginner", 6),
    ("In 'Homer the Great', what secret society does Homer join?", "Stonecutters", "beginner", 6),
    ("In 'And Maggie Makes Three', how many kids did Homer and Marge plan to have?", "Two", "beginner", 6),
    ("In 'Bart's Comet', what does Bart discover?", "Comet", "beginner", 6),
    ("In 'Homie the Clown', what does Homer dress as for a job?", "Krusty", "beginner", 6),
    ("In 'Bart vs. Australia', what country does Bart prank?", "Australia", "beginner", 6),
    ("In 'Lisa's Wedding', what country does Lisa's future husband come from?", "Scotland", "beginner", 6),
    ("In 'Treehouse of Horror VII', what does Homer get from a space alien?", "Pink donut", "beginner", 8),
    ("In 'You Only Move Twice', what agency does Homer work for?", "CIA", "beginner", 8),
    ("In 'The Homer They Fall', what sport does Homer take up?", "Boxing", "beginner", 8),
    ("In 'El Viaje Misterioso', what animal does Homer's spirit guide?", "Coyote", "beginner", 8),
    ("In 'The Springfield Files', who does Homer think he sees?", "Alien", "beginner", 8),
    ("In 'The Twisted World of Marge Simpson', what does Marge sell?", "Pretzels", "beginner", 8),
    ("In 'Mountain of Madness', where do Homer and Mr. Burns get trapped?", "Lodge", "beginner", 8),
    ("In 'Simpsoncalifragilisticexpiala', who does the family hire?", "Sherry Bobbins", "beginner", 8),
    ("In 'The Itchy and Scratchy and Poochie Show', what character is added?", "Poochie", "beginner", 8),
    ("In 'Homer's Phobia', what does John teach Bart?", "Collecting", "beginner", 8),
    ("In 'Brother from Another Series', who is Sideshow Bob's brother?", "Cecil", "beginner", 8),
    ("In 'My Sister, My Sitter', who does Lisa babysit?", "Bart and Maggie", "beginner", 8),
    ("In 'Treehouse of Horror X', what does Homer sell his soul for?", "Flaming Moe", "beginner", 11),
    ("In 'E-I-E-I-D'oh', what does Homer grow that causes trouble?", "Tomacco", "beginner", 11),
    ("In 'Hello Gutter, Hello Fadder', what sport does Homer coach?", "Baseball", "beginner", 11),
    ("In 'Eight Misbehavin'', how many babies do Apu and Manjula have?", "Eight", "beginner", 11),
    ("In 'Guess Who's Coming to Criticize Dinner', what does Homer become?", "Food critic", "beginner", 11),
    ("In 'Treehouse of Horror XII', what does Homer become?", "Jack", "beginner", 13),
    ("In 'The Frying Game', what does Marge get wrongfully convicted of?", "Murder", "beginner", 13),
    ("In 'Poppa's Got a Brand New Badge', who becomes police chief?", "Homer", "beginner", 13),
    ("In 'The Dad Who Knew Too Little', what does Homer get?", "Amnesia", "beginner", 14),
    ("In 'Treehouse of Horror XIV', what does Mr. Burns turn Bart into?", "Fly", "beginner", 15),
    ("In 'Mobile Homer', what does Homer live in?", "RV", "beginner", 16),
    ("In 'The Seemingly Never-Ending Story', what format is the episode?", "Anthology", "beginner", 17),
    ("In 'The Mook, the Chef, the Wife and Her Homer', who runs a casino?", "Fat Tony", "beginner", 18),
    ("In 'Homer the Whopper', what does Homer promote?", "Movie", "beginner", 21),
    # Intermediate
    ("In 'The Homer They Fall', who is Homer's manager for his boxing career?", "Moe", "intermediate", 8),
    ("In 'Blame It On Lisa', what is the first name of the Brazilian orphan boy Lisa sponsored?", "Ronaldo", "intermediate", 13),
    ("In 'Separate Vocations', what career result does Bart get?", "Police officer", "intermediate", 3),
    ("In 'The Telltale Head', according to the church sign, what occurs on Tuesday nights?", "Bingo", "intermediate", 1),
    ("In 'Homer's Enemy', what is Frank Grimes's job?", "Nuclear plant worker", "intermediate", 8),
    ("In 'Lisa the Vegetarian', what does Lisa give up eating?", "Meat", "intermediate", 7),
    ("In '22 Short Films About Springfield', which character gets a segment?", "Several", "intermediate", 7),
    ("In 'Much Apu About Nothing', what does Springfield vote to deport?", "Bears", "intermediate", 7),
    ("In 'Homerpalooza', what does Homer get hit in the stomach with?", "Cannonball", "intermediate", 7),
    ("In 'Summer of 4 Ft. 2', what does Lisa pretend to be?", "Jenny", "intermediate", 7),
    ("In 'Treehouse of Horror VI', what does Groundskeeper Willie claim to be?", "Lizard", "intermediate", 7),
    ("In 'Bart Sells His Soul', what does Bart sell?", "Soul", "intermediate", 7),
    ("In 'Lisa the Iconoclast', what does Lisa discover about Jebediah?", "Phony", "intermediate", 7),
    ("In 'Homer the Smithers', who does Homer work for?", "Mr. Burns", "intermediate", 7),
    ("In 'The Day the Violence Died', who sues for Itchy and Scratchy?", "Roger Meyers Sr", "intermediate", 7),
    ("In 'A Fish Called Selma', who does Troy McClure marry?", "Selma", "intermediate", 7),
    ("In 'Bart on the Road', where do the boys drive to?", "Memphis", "intermediate", 7),
    ("In 'Treehouse of Horror VIII', what does Kang say humans are?", "Cattle", "intermediate", 9),
    ("In 'The Principal and the Pauper', what is Skinner's real name?", "Armin Tamzarian", "intermediate", 9),
    ("In 'Lisa's Sax', why does the family get Lisa a saxophone?", "Bart's problems", "intermediate", 9),
    ("In 'Treehouse of Horror IX', what does Lisa turn into?", "Cat", "intermediate", 10),
    ("In 'Mayored to the Mob', who does Homer bodyguard?", "Mark Hamill", "intermediate", 10),
    ("In 'Viva Ned Flanders', what do Homer and Ned do in Vegas?", "Marry", "intermediate", 10),
    ("In 'Wild Barts Can't Be Broken', what do the kids form?", "Radio station", "intermediate", 10),
    ("In 'Sunday, Cruddy Sunday', what event do they attend?", "Super Bowl", "intermediate", 10),
    ("In 'Homer to the Max', what TV character shares Homer's name?", "Max Power", "intermediate", 10),
    ("In 'I'm With Cupid', who does Apu fall for?", "Manjula", "intermediate", 10),
    ("In 'Marge Simpson in: Screaming Yellow Honkers', what does Marge get?", "SUV", "intermediate", 10),
    ("In 'Make Room for Lisa', what does Lisa share with Homer?", "Room", "intermediate", 10),
    ("In 'Maximum Homerdrive', what does Homer drive?", "Truck", "intermediate", 10),
    ("In 'Simpsons Bible Stories', who does Homer play?", "Adam", "intermediate", 10),
    ("In 'Treehouse of Horror XI', what does Lisa's witch trial involve?", "Peach", "intermediate", 12),
    ("In 'A Tale of Two Springfields', what divides the town?", "Area code", "intermediate", 12),
    ("In 'Insane Clown Poppy', what does Krusty's father do?", "Rabbi", "intermediate", 12),
    ("In 'Lisa the Tree Hugger', what does Lisa date?", "Tree", "intermediate", 12),
    ("In 'HOMR', what does Homer have removed?", "Crayon", "intermediate", 12),
    ("In 'Trilogy of Error', how many stories does the episode tell?", "Three", "intermediate", 12),
    ("In 'Treehouse of Horror XIII', what does Mr. Burns turn into?", "Vampire", "intermediate", 14),
    ("In 'The Dad Who Knew Too Little', what country does Homer think he's in?", "France", "intermediate", 14),
    ("In 'Catch 'Em If You Can', who is the criminal?", "Sideshow Bob", "intermediate", 14),
    ("In 'Brake My Wife, Please', what does Homer become?", "Repossessor", "intermediate", 14),
    ("In 'The Great Louse Detective', who tries to kill Homer?", "Sideshow Bob", "intermediate", 14),
    ("In 'Special Edna', who does Skinner marry?", "Edna", "intermediate", 14),
    ("In 'The Regina Monologues', where does the family go?", "London", "intermediate", 15),
    ("In 'The Wandering Juvie', where does Bart get sent?", "Reform school", "intermediate", 15),
    ("In 'My Mother the Carjacker', what does Homer's mom do?", "Robs", "intermediate", 15),
    ("In 'The President Wore Pearls', who does Lisa run against?", "Martin", "intermediate", 15),
    ("In 'The Fat and the Furriest', what does Homer fight?", "Bear", "intermediate", 15),
    ("In 'Today I Am a Clown', what does Bart become?", "Krusty", "intermediate", 15),
    ("In 'Treehouse of Horror XVI', what does Mr. Burns become?", "Zombie", "intermediate", 17),
    ("In 'The Mook, the Chef, the Wife and Her Homer', what does Fat Tony run?", "Casino", "intermediate", 18),
    ("In 'Jazzy and the Pussycats', what does Lisa join?", "Band", "intermediate", 18),
    ("In 'Please Homer, Don't Hammer 'Em', what does Homer build?", "Deck", "intermediate", 18),
    ("In 'The Haw-Hawed Couple', who does Bart befriend?", "Nelson", "intermediate", 18),
    ("In 'Kill Gil, Volumes I and II', who visits for the holidays?", "Gil", "intermediate", 18),
    ("In 'The Wife Aquatic', where does Marge want to go?", "Underwater", "intermediate", 18),
    ("In 'Revenge Is a Dish Best Served Three Times', how many revenge stories?", "Three", "intermediate", 18),
    ("In 'The Boys of Bummer', what does Bart ruin?", "Game", "intermediate", 18),
    ("In 'Crook and Ladder', what does Homer become?", "Fireman", "intermediate", 18),
    ("In 'Stop or My Dog Will Shoot', what does Santa's Little Helper do?", "Act", "intermediate", 18),
    ("In '24 Minutes', what format does the episode parody?", "24", "intermediate", 18),
    ("In 'You Kent Always Say What You Want', who gets fired?", "Kent Brockman", "intermediate", 18),
    ("In 'Homer's Paternity Coot', who might be Homer's father?", "Abe", "intermediate", 18),
    ("In 'Marge Gamer', what does Marge play?", "Video game", "intermediate", 18),
    ("In 'The Burns and the Bees', what does Mr. Burns want?", "Bees", "intermediate", 20),
    ("In 'Lisa the Drama Queen', what does Lisa create?", "Imaginary world", "intermediate", 20),
    ("In 'Take My Life, Please', what does Homer discover?", "Class president", "intermediate", 20),
    ("In 'How the Test Was Won', what do the kids cheat on?", "Test", "intermediate", 20),
    ("In 'No Loan Again, Naturally', what do the Simpsons lose?", "House", "intermediate", 20),
    ("In 'Gone Maggie Gone', who kidnaps Maggie?", "Nuns", "intermediate", 20),
    ("In 'In the Name of the Grandfather', where does the family go?", "Ireland", "intermediate", 20),
    ("In 'Wedding for Disaster', who does Homer marry by accident?", "Marge", "intermediate", 20),
    ("In 'Eeny Teeny Maya Moe', what does Moe build?", "Bar", "intermediate", 20),
    ("In 'The Good, the Sad and the Drugly', who does Bart date?", "Mary", "intermediate", 20),
    # Advanced
    ("In 'The Wizard of Evergreen Terrace', what inventor does Homer idolize?", "Thomas Edison", "advanced", 10),
    ("In 'Krusty Gets Kancelled', who plays musical wine glasses on the Krusty Special?", "Hugh Hefner", "advanced", 4),
    ("In 'Marge Be Not Proud', what is Millhouse's character's INTENDED name in the video game?", "Thrillhouse", "advanced", 7),
    ("In 'Cape Feare', what does Sideshow Bob step on repeatedly?", "Rakes", "advanced", 5),
    ("In 'Rosebud', what does Mr. Burns lose?", "Teddy bear", "advanced", 5),
    ("In 'Treehouse of Horror III', what does Homer wish for?", "Finger food", "advanced", 4),
    ("In 'Mr. Plow', what is Homer's snowplow business called?", "Mr. Plow", "advanced", 4),
    ("In 'A Streetcar Named Marge', what musical does Marge star in?", "Streetcar", "advanced", 4),
    ("In 'Kamp Krusty', who runs the camp?", "Mr. Black", "advanced", 4),
    ("In 'A Fish Called Selma', what condition does Troy McClure have?", "Fish odor", "advanced", 7),
    ("In 'The Simpsons Spin-Off Showcase', what does Moe's segment parody?", "Cheers", "advanced", 8),
    ("In 'The City of New York vs. Homer Simpson', why does Homer go to NYC?", "Car", "advanced", 9),
    ("In 'Girly Edition', what do Lisa and Bart co-anchor?", "News", "advanced", 9),
    ("In 'Natural Born Kissers', where do Homer and Marge make up?", "Field", "advanced", 9),
    ("In 'Beyond Blunderdome', what movie does Homer try to fix?", "McBain", "advanced", 11),
    ("In 'Behind the Laughter', what format does the episode use?", "VH1", "advanced", 11),
    ("In 'Saddlesore Galactica', what does Lisa ride?", "Stallion", "advanced", 11),
    ("In 'Alone Again, Natura-Diddly', who dies?", "Maude", "advanced", 11),
    ("In 'Pokey Mom', what does Grampa get?", "Pacemaker", "advanced", 12),
    ("In 'Worst Episode Ever', what do the Comic Book Guy and friends form?", "Club", "advanced", 12),
    ("In 'Tennis the Menace', who does Homer play tennis with?", "Pete Sampras", "advanced", 12),
    ("In 'Day of the Jackanapes', who does Sideshow Bob try to kill?", "Krusty", "advanced", 12),
    ("In 'New Kids on the Blecch', what does Bart's band promote?", "Cigarettes", "advanced", 12),
    ("In 'Hungry, Hungry Homer', what does Homer discover about the Isotopes?", "Relocation", "advanced", 12),
    ("In 'Bye Bye Nerdie', what does Lisa fight?", "Bullying", "advanced", 12),
    ("In 'Simpson Safari', where does the family go?", "Africa", "advanced", 12),
    ("In 'Tales from the Public Domain', what three stories are parodied?", "Odyssey, Joan, Hamlet", "advanced", 13),
    ("In 'Blame It on Lisa', what city do they visit?", "Rio", "advanced", 13),
    ("In 'The Frying Game', who does Marge supposedly kill?", "Murder victim", "advanced", 13),
    ("In 'Poppa's Got a Brand New Badge', what does Homer form?", "Vigilante group", "advanced", 13),
    ("In 'The Last of the Red Hat Mamas', what club does Marge join?", "Red Hat", "advanced", 14),
    ("In 'The Strong Arms of the Ma', what does Homer's mom do?", "Rob", "advanced", 14),
    ("In 'Dude, Where's My Ranch?', what does Homer buy?", "Ranch", "advanced", 14),
    ("In 'Old Yeller-Belly', what does Homer become?", "Food critic", "advanced", 14),
    ("In 'Three Gays of the Condo', who does Homer room with?", "Grad students", "advanced", 14),
    ("In 'I'm Spelling as Fast as I Can', what does Lisa compete in?", "Spelling bee", "advanced", 14),
    ("In 'A Star Is Born Again', who does Bart meet?", "Krusty", "advanced", 14),
    ("In 'The Ziff Who Came to Dinner', who stays with the Simpsons?", "Artie", "advanced", 15),
    ("In 'Co-Dependent's Day', what does Marge become addicted to?", "Gambling", "advanced", 15),
    ("In 'The Way We Weren't', what do we learn about Homer and Marge?", "Past", "advanced", 15),
    ("In 'Fraudcast News', what does Mr. Burns buy?", "News", "advanced", 15),
    ("In 'Future-Drama', what does Bart's future self drive?", "Hovercar", "advanced", 16),
    ("In 'Mobile Homer', what does Homer live in?", "RV", "advanced", 16),
    ("In 'Million Dollar Abie', what does Grampa claim?", "Lottery", "advanced", 16),
    ("In 'Kiss Kiss, Bang Bangalore', where does Homer get outsourced?", "India", "advanced", 17),
    ("In 'The Heartbroke Kid', what does Bart get?", "Heart attack", "advanced", 16),
    ("In 'A Star Is Torn', who does Lisa meet?", "Bleeding Gums", "advanced", 6),
    ("In 'Bart's Friend Falls in Love', who does Milhouse fall for?", "Samantha", "advanced", 3),
    ("In 'Stark Raving Dad', who does Homer meet in the asylum?", "Michael Jackson", "advanced", 3),
    ("In 'Radio Bart', what does Bart get for his birthday?", "Microphone", "advanced", 3),
    ("In 'I Am Furious Yellow', what does Homer create?", "Angry Dad", "advanced", 13),
    ("In 'Scuse Me While I Miss the Sky', what does Lisa study?", "Astronomy", "advanced", 14),
    ("In 'The Seemingly Never-Ending Story', who tells the stories?", "Bart", "advanced", 17),
    ("In 'The Debarted', who is Bart's informant?", "Donny", "advanced", 19),
    ("In 'Eternal Moonshine of the Simpson Mind', what does Homer forget?", "Marge's birthday", "advanced", 19),
    ("In 'That 90's Show', what decade do we see?", "1990s", "advanced", 19),
    ("In 'Love, Springfieldian Style', what format does the episode use?", "Anthology", "advanced", 19),
    ("In 'Take My Life, Please', who was actually elected class president?", "Homer", "advanced", 20),
    ("In 'Coming to Homerica', who moves to Springfield?", "Shelbyvillians", "advanced", 20),
    ("In 'The Devil Wears Nada', what does Marge pose for?", "Painting", "advanced", 21),
    ("In 'O Brother, Where Bart Thou?', who does Homer discover?", "Half-brother", "advanced", 21),
    ("In 'Thursdays with Abie', what does Grampa write?", "Memoir", "advanced", 21),
    # Master
    ("In 'Homer's Barbershop Quartet', what was Homer's band called?", "The Be Sharps", "master", 5),
    ("In 'Homer's Barbershop Quartet', what Beatles event did the Be Sharps parody?", "Rooftop concert", "master", 5),
    ("In 'Deep Space Homer', what does Homer bring on the space mission?", "Chips", "master", 5),
    ("In 'Homer the Great', what is the Stonecutters' sacred number?", "9", "master", 6),
    ("In 'Lisa's Rival', what is Allison's project that beats Lisa's?", "Diorama", "master", 6),
    ("In 'Treehouse of Horror V', what is the time travel segment based on?", "Twilight Zone", "master", 6),
    ("In 'Sideshow Bob's Last Gleaming', what does Sideshow Bob demand?", "End TV", "master", 7),
    ("In 'The Simpsons 138th Episode Spectacular', who hosts the clip show?", "Troy McClure", "master", 7),
    ("In 'The Itchy and Scratchy and Poochie Show', when does Poochie die?", "On the way home", "master", 8),
    ("In 'Homer's Enemy', what does Frank Grimes die from?", "Electrocution", "master", 8),
    ("In 'The Canine Mutiny', what does Bart get for his dog?", "Insurance", "master", 8),
    ("In 'In Marge We Trust', what does Marge become?", "Reverend", "master", 8),
    ("In 'The Old Man and the Lisa', what does Mr. Burns recycle?", "Garbage", "master", 8),
    ("In 'Grade School Confidential', who do Skinner and Edna kiss?", "Each other", "master", 8),
    ("In 'Simpson Tide', what branch does Homer join?", "Navy", "master", 9),
    ("In 'The Trouble with Trillions', what does Homer help steal?", "Trillion", "master", 9),
    ("In 'Girly Edition', what is the name of Lisa and Bart's show?", "Smartline", "master", 9),
    ("In 'Lost Our Lisa', how does Lisa get to the museum?", "Bus", "master", 9),
    ("In 'Natural Born Kissers', what do Homer and Marge run through?", "Naked", "master", 9),
    ("In 'Thirty Minutes over Tokyo', what country do they visit?", "Japan", "master", 10),
    ("In 'They Saved Lisa's Brain', what organization does Lisa join?", "MENSA", "master", 10),
    ("In 'Maximum Homerdrive', what is the trucker's CB handle?", "Papa Wheelie", "master", 10),
    ("In 'Behind the Laughter', what causes Homer's back problem?", "Couch", "master", 11),
    ("In 'Days of Wine and D'oh'ses', what does Moe lose?", "Bar", "master", 11),
    ("In 'Worst Episode Ever', what is the Comic Book Guy's real name?", "Jeff", "master", 12),
    ("In 'HOMR', how long was the crayon in Homer's brain?", "Years", "master", 12),
    ("In 'Treehouse of Horror XII', what does the house turn into?", "Robot", "master", 13),
    ("In 'The Parent Rap', who sentences Bart and Homer?", "Judge", "master", 13),
    ("In 'The Sweetest Apu', what does Apu have to do?", "Marry", "master", 13),
    ("In 'Little Girl in the Big Ten', what college does Lisa attend?", "Springfield", "master", 13),
    ("In 'The Bart Wants What It Wants', who does Bart date?", "Greta", "master", 13),
    ("In 'The Lastest Gun in the West', who does Grampa feud with?", "Burns", "master", 13),
    ("In 'The Dad Who Knew Too Little', what does Homer think his name is?", "Dirk", "master", 14),
    ("In 'Strong Arms of the Ma', what is Mona's alias?", "Lucille", "master", 14),
    ("In 'Dude, Where's My Ranch?', what does Homer think the settlers are?", "Real", "master", 14),
    ("In 'Old Yeller-Belly', what is Homer's critic name?", "Lyle", "master", 14),
    ("In 'Catch 'Em If You Can', what does Bob steal?", "Diamond", "master", 14),
    ("In 'The Great Louse Detective', who hires Bob to find the killer?", "Homer", "master", 14),
    ("In 'Three Gays of the Condo', what are the roommates studying?", "Architecture", "master", 14),
    ("In 'I'm Spelling as Fast as I Can', what word does Lisa misspell?", "Supercalifragilisticexpialidocious", "master", 14),
    ("In 'Brake My Wife, Please', what does Homer repossess?", "Cars", "master", 14),
    ("In 'The Way We Weren't', where did young Homer and Marge meet?", "Concert", "master", 15),
    ("In 'Co-Dependent's Day', what does Marge bet on?", "Horses", "master", 15),
    ("In 'My Big Fat Geek Wedding', who does Comic Book Guy marry?", "Kumiko", "master", 15),
    ("In 'Fraudcast News', what does Burns call his media empire?", "Burns News", "master", 15),
    ("In 'Eternal Moonshine of the Simpson Mind', how does Homer try to recover his memory?", "Hypnosis", "master", 19),
    ("In 'Million Dollar Abie', what does Grampa actually win?", "Nothing", "master", 16),
    ("In 'Kiss Kiss, Bang Bangalore', what company outsources Homer?", "Nuclear plant", "master", 17),
    ("In 'The Seemingly Never-Ending Story', what is the framing device?", "Road trip", "master", 17),
    ("In 'The Debarted', what movie does the episode parody?", "Departed", "master", 19),
    ("In 'Eternal Moonshine of the Simpson Mind', what does Homer use to remember?", "Hypnosis", "master", 19),
    ("In 'That 90's Show', what band does Homer form?", "Sadgasm", "master", 19),
    ("In 'Coming to Homerica', what do the Shelbyvillians bring?", "Barley", "master", 20),
    ("In 'O Brother, Where Bart Thou?', what is the brother's name?", "Herb", "master", 21),
    # Seasons 3-9 expansion (200 additional questions)
    ("In 'Stark Raving Dad', what color shirt does Homer wear to work?", "Pink", "beginner", 3),
    ("In 'Mr. Lisa Goes to Washington', what contest does Lisa win?", "Essay", "beginner", 3),
    ("In 'When Flanders Failed', what business does Ned open?", "Leftorium", "beginner", 3),
    ("In 'Bart the Murderer', where does Bart work after school?", "Moe's", "beginner", 3),
    ("In 'Homer Defined', what does Homer accidentally do at the plant?", "Save it", "beginner", 3),
    ("In 'Like Father, Like Clown', what religion is Krusty?", "Jewish", "beginner", 3),
    ("In 'Treehouse of Horror II', what does Bart wish for?", "Brother", "beginner", 3),
    ("In 'Lisa's Pony', what does Homer get a second job to afford?", "Pony", "beginner", 3),
    ("In 'Saturdays of Thunder', what does Homer build for Bart?", "Soapbox car", "beginner", 3),
    ("In 'Flaming Moe's', what is the secret ingredient in Flaming Moe?", "Cough syrup", "beginner", 3),
    ("In 'Burns Verkaufen der Kraftwerk', who buys the plant?", "Germans", "beginner", 3),
    ("In 'I Am Furious Yellow', what color does Homer turn when angry?", "Yellow", "beginner", 3),
    ("In 'The Otto Show', what does Otto lose?", "License", "beginner", 3),
    ("In 'Bart's Friend Falls in Love', who does Milhouse fall for?", "Samantha", "beginner", 3),
    ("In 'Brother, Can You Spare Two Dimes?', who gets the money?", "Herb", "beginner", 3),
    ("In 'Lisa the Greek', what does Homer bet on with Lisa?", "Football", "beginner", 3),
    ("In 'Homer at the Bat', what team does Mr. Burns field?", "Softball", "beginner", 3),
    ("In 'Separate Vocations', what does Lisa get on her career test?", "Police", "beginner", 3),
    ("In 'Dog of Death', what does the family enter Santa's Little Helper in?", "Lottery", "beginner", 3),
    ("In 'Colonel Homer', what does Lurleen sing about?", "Homer", "beginner", 3),
    ("In 'Black Widower', who tries to kill Selma?", "Sideshow Bob", "beginner", 3),
    ("In 'The Principal and the Pauper', what does Skinner claim?", "Identity", "beginner", 3),
    ("In 'Lisa's Sax', what color is Lisa's saxophone?", "Gold", "beginner", 3),
    ("In 'Treehouse of Horror VIII', what do Kang and Kodos want?", "Election", "beginner", 9),
    ("In 'The Cartridge Family', what does Homer buy?", "Gun", "beginner", 9),
    ("In 'Bart Star', what position does Bart play?", "Quarterback", "beginner", 9),
    ("In 'The Two Mrs. Nahasapeemapetilons', who does Apu marry?", "Manjula", "beginner", 9),
    ("In 'Lisa the Skeptic', what do they dig up?", "Angel", "beginner", 9),
    ("In 'Realty Bites', what does Marge sell?", "Houses", "beginner", 9),
    ("In 'Miracle on Evergreen Terrace', what burns down?", "Tree", "beginner", 9),
    ("In 'All Singing, All Dancing', what format is the episode?", "Clip show", "beginner", 9),
    ("In 'Bart Carny', where does the family work?", "Carnival", "beginner", 9),
    ("In 'The Joy of Sect', what cult does Homer join?", "Movementarians", "beginner", 9),
    ("In 'Das Bus', what do the kids crash on?", "Island", "beginner", 9),
    ("In 'The Last Temptation of Krust', what does Krusty do?", "Retire", "beginner", 9),
    ("In 'Dumbbell Indemnity', what does Homer become?", "Insurance agent", "beginner", 9),
    ("In 'Lisa the Simpson', what does Lisa worry she has?", "Simpson gene", "beginner", 9),
    ("In 'This Little Wiggy', who does Bart befriend?", "Ralph", "beginner", 9),
    ("In 'Simpson Tide', what does Homer accidentally do?", "Sink sub", "beginner", 9),
    ("In 'The Trouble with Trillions', what does Homer help steal?", "Money", "beginner", 9),
    ("In 'Girly Edition', what do Bart and Lisa compete for?", "News show", "beginner", 9),
    ("In 'Trash of the Titans', what does Homer become?", "Sanitation commissioner", "beginner", 9),
    ("In 'King of the Hill', what does Homer climb?", "Mountain", "beginner", 9),
    ("In 'Lost Our Lisa', where does Lisa go?", "Museum", "beginner", 9),
    ("In 'Natural Born Kissers', what do Homer and Marge do?", "Reconnect", "beginner", 9),
    ("In 'Radio Bart', what does Bart use to fake being trapped?", "Microphone", "intermediate", 3),
    ("In 'Lisa the Greek', what team does Homer bet against?", "Washington", "intermediate", 3),
    ("In 'Homer at the Bat', which MLB star gets knocked out?", "Ken Griffey Jr", "intermediate", 3),
    ("In 'Homer at the Bat', what happens to Darryl Strawberry?", "Coma", "intermediate", 3),
    ("In 'Homer at the Bat', who replaces the players?", "Ringers", "intermediate", 3),
    ("In 'Separate Vocations', what does Bart become?", "Hall monitor", "intermediate", 3),
    ("In 'Colonel Homer', what is Lurleen's profession?", "Singer", "intermediate", 3),
    ("In 'Black Widower', how does Bob try to kill Selma?", "Bomb", "intermediate", 3),
    ("In 'Brother, Can You Spare Two Dimes?', what does Herb invent?", "Baby translator", "intermediate", 3),
    ("In 'Kamp Krusty', who impersonates Krusty?", "Mr. Black", "intermediate", 4),
    ("In 'A Streetcar Named Marge', what play does Marge star in?", "Streetcar", "intermediate", 4),
    ("In 'Homer the Heretic', what does Homer skip?", "Church", "intermediate", 4),
    ("In 'Lisa the Beauty Queen', what does Lisa enter?", "Pageant", "intermediate", 4),
    ("In 'Treehouse of Horror III', what does Homer wish for?", "Finger food", "intermediate", 4),
    ("In 'Itchy and Scratchy: The Movie', what do Bart and Lisa argue about?", "Movie", "intermediate", 4),
    ("In 'Marge Gets a Job', where does Marge work?", "Plant", "intermediate", 4),
    ("In 'New Kid on the Block', who moves in next door?", "Laura", "intermediate", 4),
    ("In 'Mr. Plow', what is Barney's plow business called?", "Plow King", "intermediate", 4),
    ("In 'Lisa's First Word', what is Maggie's first word?", "Daddy", "intermediate", 4),
    ("In 'Homer's Triple Bypass', what surgery does Homer need?", "Heart", "intermediate", 4),
    ("In 'Marge vs. the Monorail', who sells the monorail?", "Lyle Lanley", "intermediate", 4),
    ("In 'Selma's Choice', what does Selma ride at Duff Gardens?", "Log ride", "intermediate", 4),
    ("In 'Brother from the Same Planet', what is Tom's job?", "Big Brother", "intermediate", 4),
    ("In 'I Love Lisa', what holiday is the episode about?", "Valentine's", "intermediate", 4),
    ("In 'Duffless', what does Homer win?", "Contest", "intermediate", 4),
    ("In 'Last Exit to Springfield', what do the workers strike for?", "Dental", "intermediate", 4),
    ("In 'So It's Come to This', what holiday is it?", "April Fool's", "intermediate", 4),
    ("In 'The Front', who writes for Itchy and Scratchy?", "Bart and Lisa", "intermediate", 4),
    ("In 'Whacking Day', what do they whack?", "Snakes", "intermediate", 4),
    ("In 'Marge in Chains', what does Marge get convicted of?", "Stealing", "intermediate", 4),
    ("In 'Krusty Gets Kancelled', who replaces Krusty?", "Gabbo", "intermediate", 4),
    ("In 'Homer's Barbershop Quartet', what was Homer's band?", "Be Sharps", "intermediate", 5),
    ("In 'Cape Feare', how many rakes does Bob step on?", "Many", "intermediate", 5),
    ("In 'Homer Goes to College', what does Homer study?", "Nuclear", "intermediate", 5),
    ("In 'Rosebud', what does Mr. Burns search for?", "Bear", "intermediate", 5),
    ("In 'Treehouse of Horror IV', what is the first segment?", "Demon", "intermediate", 5),
    ("In 'Marge on the Lam', who does Marge run from police with?", "Ruth", "intermediate", 5),
    ("In 'Bart's Inner Child', who gives the self-help seminar?", "Brad Goodman", "intermediate", 5),
    ("In 'Boy-Scoutz N the Hood', what does Bart join?", "Scouts", "intermediate", 5),
    ("In 'The Last Temptation of Homer', who tempts Homer?", "Mindy", "intermediate", 5),
    ("In '$pringfield', what does Homer invest in?", "Casino", "intermediate", 5),
    ("In 'Homer the Vigilante', what does Homer form?", "Neighborhood watch", "intermediate", 5),
    ("In 'Bart Gets Famous', how does Bart become famous?", "Krusty", "intermediate", 5),
    ("In 'Deep Space Homer', what does Homer bring to space?", "Chips", "intermediate", 5),
    ("In 'Homer Loves Flanders', what does Homer do?", "Befriend Ned", "intermediate", 5),
    ("In 'Bart Gets an Elephant', what does Bart win?", "Elephant", "intermediate", 5),
    ("In 'Burns' Heir', who does Mr. Burns choose?", "Bart", "intermediate", 5),
    ("In 'Sweet Seymour', who does Skinner fall for?", "Edna", "intermediate", 5),
    ("In 'The Boy Who Knew Too Much', what does Bart witness?", "Crime", "intermediate", 5),
    ("In 'Lady Bouvier's Lover', who does Grampa date?", "Jacqueline", "intermediate", 5),
    ("In 'Secrets of a Successful Marriage', what does Homer teach?", "Marriage", "intermediate", 5),
    ("In 'Bart's Comet', what does Bart discover?", "Comet", "intermediate", 6),
    ("In 'Homer's Enemy', what is Frank Grimes's first name?", "Frank", "intermediate", 8),
    ("In 'The Simpsons Spin-Off Showcase', what does Moe's segment parody?", "Cheers", "intermediate", 8),
    ("In 'The Old Man and the Lisa', what does Mr. Burns recycle?", "Garbage", "intermediate", 8),
    ("In 'In Marge We Trust', what does Marge become?", "Reverend", "intermediate", 8),
    ("In 'The Canine Mutiny', what does Bart get for Santa's Little Helper?", "Laddie", "intermediate", 8),
    ("In 'The Springfield Files', what does Homer think he sees?", "Alien", "intermediate", 8),
    ("In 'The Twisted World of Marge Simpson', what does Marge sell?", "Pretzels", "intermediate", 8),
    ("In 'Mountain of Madness', where do Homer and Burns get stuck?", "Lodge", "intermediate", 8),
    ("In 'Simpsoncalifragilisticexpiala', what does Sherry Bobbins stand for?", "Nanny", "intermediate", 8),
    ("In 'The Itchy and Scratchy and Poochie Show', when does Poochie die?", "Driving home", "intermediate", 8),
    ("In 'Homer's Phobia', what does John collect?", "Bear", "intermediate", 8),
    ("In 'Brother from Another Series', who is Bob's brother?", "Cecil", "intermediate", 8),
    ("In 'My Sister, My Sitter', who does Lisa babysit?", "Bart and Maggie", "intermediate", 8),
    ("In 'Homer's Enemy', what kills Frank Grimes?", "Electricity", "intermediate", 8),
    ("In 'The City of New York vs. Homer Simpson', why does Homer go to NYC?", "Car", "intermediate", 9),
    ("In 'The Principal and the Pauper', what is Skinner's real name?", "Armin", "intermediate", 9),
    ("In 'Lisa's Sax', why does the family get Lisa a sax?", "Bart", "intermediate", 9),
    ("In 'Treehouse of Horror IX', what does Lisa turn into?", "Cat", "intermediate", 9),
    ("In 'When You Dish Upon a Star', who do the Simpsons meet?", "Celebrities", "intermediate", 9),
    ("In 'D'oh-in in the Wind', what does Homer search for?", "Mother", "intermediate", 9),
    ("In 'Lisa the Simpson', what chromosome does Lisa worry about?", "Y", "intermediate", 9),
    ("In 'Simpson Tide', what branch does Homer join?", "Navy", "intermediate", 9),
    ("In 'The Trouble with Trillions', what denomination do they steal?", "Trillion", "intermediate", 9),
    ("In 'Girly Edition', what is the show called?", "Smartline", "intermediate", 9),
    ("In 'Lost Our Lisa', how does Lisa get to the museum?", "Bus", "intermediate", 9),
    ("In 'Natural Born Kissers', what do Homer and Marge run through?", "Cornfield", "intermediate", 9),
    ("In 'Thirty Minutes over Tokyo', what country do they visit?", "Japan", "intermediate", 9),
    ("In 'Bart the Murderer', who does Bart supposedly kill?", "Nobody", "advanced", 3),
    ("In 'When Flanders Failed', what does Ned sell at the Leftorium?", "Left-handed products", "advanced", 3),
    ("In 'Flaming Moe's', what does Moe rename his drink?", "Flaming Moe", "advanced", 3),
    ("In 'Homer at the Bat', who gets radiation poisoning?", "Don Mattingly", "advanced", 3),
    ("In 'Homer at the Bat', who gets arrested?", "Wade Boggs", "advanced", 3),
    ("In 'Black Widower', what does Bob use as the murder weapon?", "Bomb", "advanced", 3),
    ("In 'Colonel Homer', what is Lurleen's hit song?", "Burning Love", "advanced", 3),
    ("In 'Brother, Can You Spare Two Dimes?', what does Herb's invention do?", "Translates", "advanced", 3),
    ("In 'Kamp Krusty', what do the kids revolt over?", "Conditions", "advanced", 4),
    ("In 'Mr. Plow', what song plays in Homer's commercial?", "Mr. Plow", "advanced", 4),
    ("In 'A Streetcar Named Marge', what does Marge play?", "Blanche", "advanced", 4),
    ("In 'Marge vs. the Monorail', what powers the monorail?", "Magnetism", "advanced", 4),
    ("In 'Last Exit to Springfield', who leads the dental strike?", "Lenny", "advanced", 4),
    ("In 'So It's Come to This', what does Bart say on TV?", "Dead", "advanced", 4),
    ("In 'The Front', what pseudonym do Bart and Lisa use?", "Writers", "advanced", 4),
    ("In 'Krusty Gets Kancelled', what does Gabbo say?", "Gabbo", "advanced", 4),
    ("In 'Homer's Barbershop Quartet', what Beatles event do they parody?", "Rooftop", "advanced", 5),
    ("In 'Cape Feare', what movie does the episode parody?", "Cape Fear", "advanced", 5),
    ("In 'Rosebud', what is the bear's name?", "Bobo", "advanced", 5),
    ("In 'Deep Space Homer', what does Homer do that alarms NASA?", "Floats", "advanced", 5),
    ("In 'Homer the Vigilante', who is the real thief?", "Moleman", "advanced", 5),
    ("In 'Bart Gets an Elephant', what do they name the elephant?", "Stampy", "advanced", 5),
    ("In 'Burns' Heir', what does Bart inherit?", "Estate", "advanced", 5),
    ("In 'Homer the Heretic', what does God tell Homer?", "Go to church", "advanced", 4),
    ("In 'Lisa's First Word', what is Bart's first word?", "Ay caramba", "advanced", 4),
    ("In 'Marge in Chains', what does Marge steal?", "Bourbon", "advanced", 4),
    ("In 'Homer's Triple Bypass', who performs the surgery?", "Hibbert", "advanced", 4),
    ("In 'Homer the Great', what is the Stonecutters' number?", "9", "advanced", 6),
    ("In 'Lisa's Rival', who beats Lisa's project?", "Allison", "advanced", 6),
    ("In 'Treehouse of Horror V', what is the time travel segment?", "Twilight Zone", "advanced", 6),
    ("In 'Sideshow Bob's Last Gleaming', what does Bob demand?", "No TV", "advanced", 7),
    ("In 'The Simpsons 138th Episode Spectacular', who hosts?", "Troy McClure", "advanced", 7),
    ("In 'Homer's Enemy', what does Frank Grimes work as?", "Engineer", "advanced", 8),
    ("In 'The Canine Mutiny', what does Laddie have?", "Insurance", "advanced", 8),
    ("In 'In Marge We Trust', what does Marge preach?", "Forgiveness", "advanced", 8),
    ("In 'The Old Man and the Lisa', what does Burns make from garbage?", "Product", "advanced", 8),
    ("In 'Grade School Confidential', who kisses in the closet?", "Skinner and Edna", "advanced", 8),
    ("In 'The Simpsons Spin-Off Showcase', what happens to the Simpsons?", "Cleveland", "advanced", 8),
    ("In 'The Itchy and Scratchy and Poochie Show', what is Poochie?", "Dog", "advanced", 8),
    ("In 'Homer's Phobia', what is John's sexual orientation?", "Gay", "advanced", 8),
    ("In 'Brother from Another Series', what does Cecil frame Bob for?", "Bombing", "advanced", 8),
    ("In 'The City of New York vs. Homer Simpson', where does Homer park?", "World Trade Center", "advanced", 9),
    ("In 'The Principal and the Pauper', who was the real Skinner?", "Soldier", "advanced", 9),
    ("In 'Lisa the Simpson', what does the Y chromosome cause?", "Stupidity", "advanced", 9),
    ("In 'Simpson Tide', what does Homer do to the sub?", "Sinks", "advanced", 9),
    ("In 'The Trouble with Trillions', what does Homer help steal?", "Trillion", "advanced", 9),
    ("In 'Girly Edition', what do Bart and Lisa fight over?", "News", "advanced", 9),
    ("In 'Natural Born Kissers', where do Homer and Marge make love?", "Field", "advanced", 9),
    ("In 'Thirty Minutes over Tokyo', what do they do in Japan?", "Game show", "advanced", 9),
    ("In 'They Saved Lisa's Brain', what group does Lisa join?", "MENSA", "advanced", 10),
    ("In 'Stark Raving Dad', what is the man's real identity?", "Leon Kompowsky", "master", 3),
    ("In 'Homer at the Bat', what causes the players to miss the game?", "Various", "master", 3),
    ("In 'Flaming Moe's', what ingredient makes Flaming Moe special?", "Cough syrup", "master", 3),
    ("In 'Colonel Homer', what is Lurleen Lumpkin's profession?", "Country singer", "master", 3),
    ("In 'Black Widower', what is Sideshow Bob's plan?", "Kill Selma", "master", 3),
    ("In 'Kamp Krusty', what does Bart trade for?", "Krusty doll", "master", 4),
    ("In 'Mr. Plow', what does Barney call his plow?", "Plow King", "master", 4),
    ("In 'Last Exit to Springfield', what do the workers win?", "Dental plan", "master", 4),
    ("In 'Krusty Gets Kancelled', who is Krusty's rival?", "Gabbo", "master", 4),
    ("In 'Homer's Barbershop Quartet', what year did the Be Sharps break up?", "1985", "master", 5),
    ("In 'Cape Feare', how does Bob get to the Simpsons?", "Boat", "master", 5),
    ("In 'Deep Space Homer', what snack does Homer open in space?", "Chips", "master", 5),
    ("In 'Homer the Great', what do the Stonecutters do at meetings?", "Rituals", "master", 6),
    ("In 'Lisa's Rival', what is Allison's diorama of?", "Itchy and Scratchy", "master", 6),
    ("In 'Sideshow Bob's Last Gleaming', what does Bob want to destroy?", "Television", "master", 7),
    ("In 'Homer's Enemy', what is Frank Grimes's nickname?", "Grimey", "master", 8),
    ("In 'The Canine Mutiny', what happens to Laddie?", "Returned", "master", 8),
    ("In 'The Itchy and Scratchy and Poochie Show', what happens to Poochie?", "Dies", "master", 8),
    ("In 'The Principal and the Pauper', what is Armin Tamzarian's job?", "Soldier", "master", 9),
    ("In 'The City of New York vs. Homer Simpson', what building has Homer's car?", "Twin Towers", "master", 9),
    ("In 'Natural Born Kissers', what do Homer and Marge run through naked?", "Stadium", "master", 9),
    ("In 'Thirty Minutes over Tokyo', what show do they go on?", "Takeshi", "master", 9),
]

_frink_active = True
_frink_daily_enabled = False
_frink_difficulty: Optional[str] = None  # beginner | intermediate | advanced | master
_frink_seasons: Optional[list[int]] = None  # e.g. [1, 2, 3] or None for all

# Active question per room_id: {"answer": str, "question_msg_id": int} — cleared when answered or timeout
_active_trivia: dict[int, dict] = {}

# Multi-round sessions: room_id -> rounds left to post after current (for !trivia X)
_trivia_rounds_remaining: dict[int, int] = {}
# Total rounds for current session (for "Round X of Y" prefix)
_trivia_total_rounds: dict[int, int] = {}

# Hot streaks: (room_id, user_id) -> consecutive correct count
_trivia_streak: dict[tuple[int, int], int] = {}

# When nobody gets it right and Frink has to reveal the answer
RIDICULE_PHRASES = [
    "Glavin! Not a single correct answer! The flux capacitor weeps!",
    "Hoyvin! The collective knowledge of this room has failed the mathematics of trivia!",
    "By Jove—I mean, by science! Did anyone here watch the show?!",
    "Ooh, the cosmic ballet of incorrect answers! A most disappointing outcome!",
    "Shabooey! Zero correct! The thingamajig is most unimpressed!",
    "Eureka! Well, almost—nobody got it. The probability was not in your favor!",
    "Glaaven! Such a simple question, and yet—silence. Glavin!",
    "The mathematics never lie—and neither does the answer you all missed!",
    "Fascinating! Absolutely fascinating how wrong everyone was!",
    "Yes, yes! The flux capacitor—I mean, your brains—need a tune-up!",
    "I've invented a way to look into the future! It turns out nobody got it. Oops, spoilers!",
    "Why won't people listen to my warnings? Is it the glasses? The bow tie? The way I say 'glaven'?",
    "I'm sorry, I can't hear you over the sound of my own genius! ...and your wrong answers.",
    "Everything is under control! Except for the screaming and the wrong answers!",
]

HOT_STREAK_PHRASES = [
    "Ooh, the mathematics of a hot streak! Glavin!",
    "Two in a row! The probability is most favorable!",
    "Three consecutive! The flux capacitor approves!",
    "Four! Four! Hoyvin-glaven!",
    "Five! A pentagon of perfection!",
    "Six! The hex of knowledge!",
    "Seven! A week of wisdom! Shabooey!",
    "The cosmic ballet of correct answers continues!",
    "Eureka! The thingamajig is buzzing with approval!",
    "By science—a most favorable outcome!",
    "The flux capacitor never lies! Glaaven!",
    "It's elementary physics, really. If you increase the velocity, you increase the hoo-ha!",
    "I'm sorry, I can't hear you over the sound of my own genius! ...and your correct answers!",
    "The mathematics never lie—and neither do you!",
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
    Uses placeholder data. API contract for simpsons-trivia.com integration when available.
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


def set_frink_difficulty(difficulty: Optional[str]) -> None:
    global _frink_difficulty
    if difficulty in ("beginner", "intermediate", "advanced", "master", None):
        _frink_difficulty = difficulty


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
    """Return a random Frink-y reply for DMs. Mix of greetings and show quotes."""
    dm_replies = [
        "Glavin! The flux capacitor is buzzing! What can this humble scientist do for you?",
        "Hoyvin! A message! Ooh, the mathematics of communication!",
        "Yes, yes! You've reached the lab. The thingamajig is at your service!",
        "Shabooey! Prof Frink here, ready to assist with all matters scientific!",
        "Glaaven! Your message has been received. The probability of a reply is 100%!",
        "The cosmic ballet of DMs! A most scientific greeting to you!",
        "Eureka! Well, almost—Prof Frink at your service, glavin!",
        "By Jove—I mean, by science! Your message has arrived. How may I assist?",
        "The flux capacitor approves of your correspondence! Hoyvin!",
        "A message! The mathematics of friendship are most favorable!",
    ]
    # 40% chance of a classic Frink quote from the show
    if random.random() < 0.4 and FRINK_QUOTES:
        return format_frink_reply(random.choice(FRINK_QUOTES), include_frinkism=random.random() < 0.3)
    return random.choice(dm_replies)


def get_trivia_total_rounds(room_id: int) -> int:
    """Total rounds for current multi-round session (0 if single round)."""
    return _trivia_total_rounds.get(room_id, 0)


def set_trivia_total_rounds(room_id: int, n: int) -> None:
    """Set total rounds for multi-round session."""
    global _trivia_total_rounds
    if n <= 0:
        _trivia_total_rounds.pop(room_id, None)
    else:
        _trivia_total_rounds[room_id] = n


def get_trivia_response(room_id: Optional[int] = None) -> tuple[str, str]:
    """
    Fetch a trivia question and return (question_message, answer_for_later).
    When room_id has a multi-round session (total > 1), prefix with "Round X of Y".
    """
    tq = fetch_trivia_question()
    if not tq:
        return format_frink_reply("The trivia flux capacitor is on the fritz! Try again later, glavin!"), ""
    total = get_trivia_total_rounds(room_id) if room_id else 0
    remaining = get_trivia_rounds_remaining(room_id) if room_id else 0
    round_prefix = ""
    if total > 1 and remaining >= 0:
        current = total - remaining  # 1-based: round 1, 2, 3...
        round_prefix = f"**Round {current} of {total}** — "
    msg = format_frink_reply(f"{round_prefix}**Trivia time!** {tq.question} You have {TRIVIA_SECONDS} seconds!")
    return msg, tq.answer


def get_trivia_timeout_reply(answer: str) -> str:
    """When nobody got it right, ridicule the room and reveal the answer."""
    ridicule = random.choice(RIDICULE_PHRASES)
    return f"{ridicule}\n\n**Answer:** {answer}"


def set_active_trivia(room_id: int, answer: str, question_msg_id: int) -> None:
    """Record active question for answer matching. Stores end_time for timer UI."""
    global _active_trivia
    end_time = time.time() + TRIVIA_SECONDS
    _active_trivia[room_id] = {"answer": answer, "question_msg_id": question_msg_id, "end_time": end_time}


def get_trivia_phase_info(room_id: int) -> dict | None:
    """Return {end_time} for timer UI if trivia is active, else None."""
    active = _active_trivia.get(room_id)
    if not active or "end_time" not in active:
        return None
    return {"end_time": active["end_time"]}


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


def set_trivia_rounds_remaining(room_id: int, n: int, total: Optional[int] = None) -> None:
    """Set rounds left for multi-round session. Optionally set total (for Round X of Y)."""
    global _trivia_rounds_remaining, _trivia_total_rounds
    if n <= 0:
        _trivia_rounds_remaining.pop(room_id, None)
        # Keep total until last round is posted (cleared by clear_trivia_session)
    else:
        _trivia_rounds_remaining[room_id] = n
        if total is not None:
            _trivia_total_rounds[room_id] = total


def clear_trivia_session(room_id: int) -> None:
    """Clear total rounds when session ends (after last round posted)."""
    global _trivia_total_rounds
    _trivia_total_rounds.pop(room_id, None)


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
        "**Commands** (in #Trivia or configured channels; ! and / both work):",
        "• **!trivia** or **!trivia X** (X=1–7) — Fetch one or X consecutive Simpsons trivia questions (first correct answer wins; 45s per question, 400+ questions)",
        "• **!daily** — Toggle daily automated trivia post (admin or frink_control)",
        "• **!set-difficulty [beginner|intermediate|advanced|master]** — Filter by difficulty",
        "• **!set-seasons [1-20]** — Filter by season(s), e.g. !set-seasons 1 2 3",
        "• **!settings** — Show current bot configuration",
        "• **!score** or **/score** — Show trivia leaderboard",
        "• **!help** or **!commands** — This message",
        "",
        "The mathematics of knowledge await! Hoyvin-glaven!",
    ])
