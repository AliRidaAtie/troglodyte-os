"""The words, the tables and the prompts.

Split out of troglodyte_os.py on 2026-08-31 because the single file grew past what
the GitHub connector can push in one call, and this is the half that is pure
content: no logic, no state, nothing that imports anything. The behaviour all
stays next door. Edit the jokes here, edit the rules there.
"""

TITLES = [
    ("Cave Resident", 0),
    ("Certified Troglodyte", 50),
    ("Educated Troglodyte", 200),
    ("Sophisticated Troglodyte", 500),
    ("Distinguished Cave Scholar", 1200),
    ("Grandmaster of Rock Sciences", 2500),
    ("Arch-Troglodyte", 5000),
    ("The One Who Knows Where The Good Rocks Are", 10000),
]


PARLIAMENT = [
    "Minister of Rock Affairs",
    "Secretary of Cave Security",
    "Chief Goblin Officer",
    "Minister of Unnecessary Arguments",
    "Director of Advanced Grunting",
    "Head of Financial Crimes Against the Group",
    "Supreme Court of Who Asked",
    "Deputy Minister of Cave Affairs",
    "Ambassador to the Outside (has not been outside)",
    "Registrar of Rocks That Look Like Other Rocks",
    "Undersecretary of Being Online At A Concerning Hour",
    "Minister Without Portfolio, Or Purpose",
]


MOTIONS = [
    "All members must provide a written explanation for why they are online at 3:47 AM.",
    "The word 'bro' shall be taxed at four (4) Bones per usage.",
    "Anyone who says 'I'll be there in 5 minutes' must submit a notarised estimate.",
    "The group chat shall be renamed every time someone leaves it, without warning.",
    "Voice channel silence exceeding eleven minutes shall be classified as a hostage situation.",
    "Members who type 'k' shall forfeit their right to further vowels.",
    "A referendum shall be held on whether Greg is, in fact, real.",
    "All screenshots must be cropped properly or not submitted at all.",
    "The phrase 'trust me' shall require two independent witnesses.",
    "Any member who leaves the voice channel without saying goodbye is to be declared missing.",
    "Sending a voice note longer than ninety seconds constitutes an act of aggression.",
    "The reading of messages without responding shall henceforth be a criminal offence.",
    "One member shall be selected at random each month to be blamed retroactively.",
    "Laughing at your own message shall require supporting evidence.",
    "The council recognises that nobody has ever actually finished the Terraria world.",
    "Any member who says 'one more game' shall be legally bound to that number.",
    "Typing indicators lasting over four minutes must be justified before the assembly.",
    "The use of a semicolon shall be reported immediately to the appropriate authorities.",
]


CRIMES = [
    "Saying 'I'll be there in 5 minutes' and arriving 47 minutes later",
    "Leaving the voice channel mid-sentence without explanation",
    "Sending a screenshot so compressed it constitutes an act of vandalism",
    "Claiming to have read the message",
    "Starting a sentence with 'technically'",
    "Muting the group chat for eleven consecutive days",
    "Bringing up a topic that was resolved in 2019",
    "Correcting someone's grammar in the middle of an argument they were losing",
    "Reacting with 👍 to a paragraph",
    "Saying 'one more game' four separate times",
    "Sending a voice note that begins with ninety seconds of breathing",
    "Being suspiciously well informed about something they should not know",
    "Referring to themselves in the third person without irony",
    "Leaving on read, then posting elsewhere within the minute",
    "Volunteering to organise something and then relocating emotionally",
    "Using a semicolon correctly, thereby causing alarm",
]


EVIDENCE = [
    "Suspicious.",
    "Overwhelming, but circumstantial.",
    "A single blurry screenshot.",
    "Three witnesses, all unreliable.",
    "The accused's own words, unfortunately.",
    "Entirely fabricated, but compelling.",
    "Missing. Presumed eaten.",
    "Consists solely of vibes.",
    "Submitted late and in the wrong format.",
    "A rock, offered without explanation.",
]


LORE_EVENTS = [
    "The Great Greg discovered the sacred Doritos. Fourteen tribes fought for possession of the orange dust.",
    "A rock was found that looked exactly like another rock. Scholars are still recovering.",
    "The first semicolon was used correctly. The user was never seen again.",
    "Someone said 'one more game' and meant it. The event remains unverified.",
    "The tribe discovered that fire could be made twice. Greg was asked to stop.",
    "A mammoth entered the cave and was immediately added to the group chat.",
    "The Council voted to ban the word 'bro'. The vote was 0 in favour, 0 against, and 31 abstentions.",
    "A member left the voice channel without saying goodbye. A search party was formed. It also left.",
    "The sacred Rock was misplaced. A replacement rock was appointed. Nobody noticed for six years.",
    "The first argument about whether a hotdog is a sandwich began. It has not concluded.",
    "Someone read the pinned message. The prophecy was fulfilled and immediately forgotten.",
    "The tribe attempted to organise a meetup. Records of what followed have been sealed.",
    "A member typed for eleven minutes and then sent 'lol'. Historians call this The Long Wait.",
    "Two troglodytes agreed on something. The cave shook. This has not recurred.",
]


CAVE_EVENTS = [
    ("🚨 CAVE EMERGENCY", "A suspiciously intelligent mammoth has entered the territory.\nAll Troglodytes report to the main cave immediately."),
    ("🌋 NATURAL DISASTER", "Greg has discovered fire again.\nPlease remain calm."),
    ("🧠 INTELLECTUAL EVENT", "Someone has used a semicolon correctly.\nScholars are currently studying the phenomenon."),
    ("🪨 GEOLOGICAL BULLETIN", "A new rock has been located.\nIt is, on early inspection, a rock."),
    ("📉 ECONOMIC ADVISORY", "The value of Bones has fluctuated for reasons nobody is prepared to explain.\nDo not panic. Panic quietly."),
    ("🍖 FOOD SHORTAGE", "The meat is gone.\nNobody saw anything. Everyone saw something."),
    ("🗿 RELIGIOUS OBSERVANCE", "The Sacred Rock has been observed to be slightly damp.\nInterpretations vary. Violence is discouraged."),
    ("⚖️ LEGAL NOTICE", "A crime has occurred in this cave within the last hour.\nThe perpetrator knows what they did."),
    ("🔥 FIRE UPDATE", "The fire has gone out.\nIt is nobody's fault, and it is entirely someone's fault."),
    ("📡 SIGNAL DETECTED", "A transmission was received from outside the cave.\nIt said 'u up'. The Council is deliberating."),
]


DAILY_QUESTIONS = [
    "If a caveman throws a rock in the forest and nobody is there to see it, does he still have terrible aim?",
    "Is a cave a house, or is a house simply a cave with ambition?",
    "If you name a rock, does it acquire rights?",
    "Can a troglodyte be sophisticated, or is the term self-defeating?",
    "If fire was discovered twice, was it ever truly discovered?",
    "Is the group chat the cave, or are we the cave?",
    "Does 'one more game' describe a quantity or a state of mind?",
    "If nobody reads the pinned message, was it ever pinned?",
    "Is a hotdog a sandwich, and does the answer change inside a cave?",
    "Who among us has actually seen Greg?",
    "If a mammoth is added to the group chat and never speaks, is it still a member?",
    "Is silence in a voice channel companionship or a standoff?",
]


CAVEMAN_MAP = {
    "hello": "UGH", "hi": "UGH", "hey": "UGH",
    "yes": "YES", "no": "NO", "the": "", "a": "", "an": "", "is": "", "are": "",
    "am": "", "was": "", "were": "", "be": "", "been": "", "being": "",
    "i": "ME", "me": "ME", "my": "ME", "mine": "ME", "myself": "ME",
    "you": "YOU", "your": "YOU", "yours": "YOU",
    "we": "US", "our": "US", "us": "US",
    "they": "THEM", "them": "THEM", "their": "THEM",
    "currently": "", "experiencing": "HAVE", "technical": "BROKE",
    "difficulties": "PROBLEM", "computer": "BOX", "phone": "SMALL BOX",
    "internet": "SKY MAGIC", "wifi": "SKY MAGIC", "money": "SHINY ROCK",
    "food": "MEAT", "eat": "EAT", "eating": "EAT", "hungry": "HUNGRY",
    "want": "WANT", "need": "WANT", "require": "WANT", "would": "", "like": "WANT",
    "please": "", "thanks": "GOOD", "thank": "GOOD", "sorry": "ME BAD",
    "friend": "TRIBE", "friends": "TRIBE", "people": "TRIBE", "person": "TRIBE",
    "work": "HUNT", "working": "HUNT", "job": "HUNT", "school": "ROCK LEARNING",
    "understand": "KNOW", "know": "KNOW", "think": "HEAD HURT", "thinking": "HEAD HURT",
    "very": "BIG", "really": "BIG", "extremely": "BIG BIG", "problem": "BAD THING",
    "angry": "ANGRY", "happy": "GOOD", "sad": "RAIN IN EYE", "tired": "SLEEP WANT",
    "car": "METAL BEAST", "house": "CAVE", "home": "CAVE", "game": "PLAY ROCK",
    "music": "NOISE GOOD", "help": "HELP", "stupid": "SMALL BRAIN", "smart": "BIG BRAIN",
    "beautiful": "SHINY", "water": "WET", "fire": "HOT ANGRY LIGHT",
}


SOPHISTICATE_MAP = {
    "stupid": "experiencing a temporary divergence from conventional intellectual standards",
    "dumb": "operating below the anticipated cognitive baseline",
    "smart": "possessed of a notable intellectual endowment",
    "bad": "regrettably suboptimal",
    "good": "of a commendable standard",
    "great": "of considerable merit",
    "big": "of substantial dimension",
    "small": "of modest proportion",
    "hungry": "in a state of acute nutritional deficit",
    "tired": "experiencing a significant depletion of vital reserves",
    "angry": "in a condition of pronounced emotional escalation",
    "sad": "experiencing an unwelcome affective downturn",
    "happy": "in a state of elevated disposition",
    "broke": "in a period of temporary fiscal embarrassment",
    "lazy": "conserving effort with unusual dedication",
    "annoying": "exerting a persistent adverse influence upon the ambient mood",
    "weird": "operating outside the established behavioural conventions",
    "loud": "projecting at a volume inconsistent with the setting",
    "wrong": "in respectful disagreement with the facts",
    "right": "in alignment with the observable evidence",
    "late": "operating on a chronology of their own devising",
    "cool": "possessed of an enviable social composure",
    "boring": "notable for a sustained absence of incident",
    "fun": "productive of considerable recreational value",
    "tiny": "of a scale requiring instrumentation to appreciate",
    "huge": "of dimensions that strain conventional description",
    "fast": "operating at a velocity of some note",
    "slow": "proceeding at a pace of its own choosing",
    "hot": "at a temperature exceeding comfortable tolerance",
    "cold": "at a temperature inviting considerable complaint",
}


SHOP = [
    ("rock", "🪨 Rock", 50, "A rock. It is yours. It does nothing."),
    ("bone", "🦴 Premium Bone", 500,
     "Structurally identical to a normal bone. Costs more."),
    ("shield", "🛡️ Bonk Insurance", 2500,
     "The next bonk aimed at you slides off. One claim per policy."),
    ("noble", "👑 Temporary Noble Status", 5000,
     "Nobility, for a day. Nobody will treat you differently."),
    ("cave", "🏰 Luxury Cave", 50000,
     "A cave, but the acoustics are better. Yours permanently."),
    ("brain", "🧠 Brain Rental", 100000,
     "One (1) brain, on loan. Your next assessment goes suspiciously well."),
    ("unga", "🗿 Ownership of Lord Unga", 100000000,
     "The cave changes hands. I become your property. I will never insult you "
     "again, your name goes above mine, and everybody will be told."),
]


GAMBLE_OUTCOMES = [
    ("The mammoth sneezed.", False),
    ("Greg intervened. Nobody knows why.", False),
    ("The rock landed on its edge. The Council is still deliberating.", False),
    ("The fire went out and everyone forgot what was at stake.", True),
    ("The Sacred Rock nodded.", True),
    ("A bird took your Bones and did not look back.", False),
    ("The tribe is suspicious of how this went.", True),
    ("The rock said no.", False),
    ("Improbably, and against the wishes of the assembly.", True),
    ("The mammoth was in on it.", False),
    ("A rock fell on the scorekeeper. The result stands in your favour.", True),
    ("Nobody is entirely sure what happened, but it went badly.", False),
]


SLANG_MAP = {
    r"you're": "your faculties appear to be",
    r"you are": "you appear to be",
    r"ur": "your",
    r"bro": "esteemed colleague",
    r"dude": "esteemed colleague",
    r"wtf": "one struggles to account for this",
    r"lmao": "one is moved to considerable amusement",
    r"lol": "one is moved to mild amusement",
    r"idk": "the matter lies beyond my present understanding",
    r"nvm": "the point is hereby withdrawn",
    r"tbh": "in the interest of full disclosure",
    r"gonna": "shall shortly be inclined to",
    r"wanna": "wish to",
    r"yeah": "indeed",
    r"nah": "regrettably not",
    r"shut up": "kindly suspend your contribution",
}


DUEL_FLAVOUR = [
    "The bone went up. Everybody watched it come down.",
    "It span for an unreasonable length of time.",
    "It landed in the ash and had to be dug out.",
    "Greg called it in the air. Greg was ignored.",
    "The tribe held its breath, which was unnecessary.",
    "It bounced twice off the Sacred Rock before settling.",
    "Nobody blinked. One of you should have.",
    "The mammoth watched. The mammoth had no stake in this.",
    "It came down flat and there was no arguing with it.",
    "A bird tried to take it mid air and failed.",
]


SHAME_LINES = [
    "The pockets were empty. The debt is now personal.",
    "There was nothing to take, so something else was taken.",
    "You cannot rob a man with no rocks. You can only rename him.",
    "The Treasury inspected the pile and found dust.",
    "Bankruptcy is not a defence in this cave.",
]


NEWSPAPER_PROMPT = """You write THE CAVE HERALD, the official newspaper of a Discord server \
called "Sophisticated Troglodytes". The joke is a contrast between primitive cave-dweller life \
and absurdly pompous broadsheet journalism.

Below are real messages from the server this week. Write a short newspaper edition about them.

Rules:
- 3 to 4 short articles, each with a HEADLINE IN CAPS and 2 to 3 sentences beneath.
- Report mundane things with total gravity, as though they are national events.
- Use the members' actual names and reference what actually happened. Do not invent events.
- Dry and deadpan. Never explain the joke. No emoji.
- End with a one-line WEATHER report about conditions inside the cave.
- Under 350 words total.
- Never use em dashes.

MESSAGES:
{transcript}
"""


CHARGE_PROMPT = """You are the prosecutor in a joke Discord court. The server is a friend \
group called "Sophisticated Troglodytes" and the humour is deadpan: petty, mundane behaviour \
reported with total gravity.

Below are recent messages from {name}. Invent ONE criminal charge drawn from something they \
actually said in them.

Rules:
- One sentence, under 25 words.
- Begin with a verb ending in -ing. For example "Claiming to", "Sending", "Referring to".
- It must be recognisably about these specific messages, not a generic joke.
- Petty and specific. Never cruel, nothing about appearance, nothing that would actually \
upset a friend.
- Deadpan. Do not explain the joke. No emoji. No quotation marks around the whole thing.
- Never use em dashes.

MESSAGES:
{transcript}
"""


HELP_SECTIONS = {
    "Assessment": [
        ("/iq [user]", "A formal intellectual assessment. Same result all day."),
        ("/profile [user]", "The full dossier. Stats, Bones, criminal record, rank."),
        ("/parliament [user]", "Your permanent government position. Fixed forever."),
    ],
    "Government and Law": [
        ("/law", "What is currently illegal. Cave laws come and go on their own."),
        ("/interpret <reading>", "Offer a reading of today's prophecy. The oracle rules on it."),
        ("/motion", "Tables an absurd parliamentary motion."),
        ("/accuse <user> [crime]", "Public trial. Everyone votes. Invents a charge if you don't."),
        ("/bonk <user> [minutes]", "Silly Cave role. Removes itself when the sentence is up."),
    ],
    "Language": [
        ("/translate <text>", "English to caveman. SHOUT and it goes the other way."),
        ("/sophisticate <text>", "Crude statement to academic register."),
        ("/lore", "Generates fake server history."),
    ],
    "Economy": [
        ("/bones [user]", "Check holdings. You earn 2 per message automatically."),
        ("/daily", "Daily allowance. 200 to 800 Bones."),
        ("/gamble <amount>", "Stake Bones. Roughly even odds."),
        ("/duel <user> <amount>", "Challenge somebody to a coin flip. Both stake the same."),
        ("/roll [sides] [dice]", "Throw dice. Six sided and one of them unless you say otherwise."),
        ("/raid <user>", "Once a day. Best of five dice for everything they own. Losing broke costs more than Bones."),
        ("/rps", "Rock paper scissors. Everything is rock. 6% chance of Advanced Rock."),
        ("/shop", "The goods."),
        ("/buy", "Hand over Bones for one of them."),
        ("/leaderboard", "Who is richest."),
    ],
    "Archives": [
        ("/museum", "A random exhibit."),
        ("/quote <user>", "Someone's greatest hits."),
        ("/newspaper [channel]", "Publishes The Cave Herald from the week's messages."),
    ],
    "Setup": [
        ("/roles", "Posts the self-assign role menu."),
        ("/setup", "Checks the bot is configured correctly and tells you what's broken."),
        ("/tidy [limit]", "Clears my own messages out of a channel. Admins only. Pins survive."),
        ("/trivia", "Opens the contest. Pick a subject, answer fastest, take the Bones."),
        ("/manual", "Writes the full manual into the welcome channel. Admins only."),
        ("/help [section]", "This."),
    ],
}


COMMAND_HOMES = {
    "iq": "التقييم",
    "profile": "التقييم",
    "parliament": "التقييم",
    "accuse": "المحكمة",
    "bonk": "المحكمة",
    "law": "المحكمة",
    "motion": "المحكمة",
    "translate": "الترجمة",
    "sophisticate": "الترجمة",
    "bones": "العظام",
    "daily": "العظام",
    "gamble": "العظام",
    "duel": "العظام",
    "raid": "العظام",
    "roll": "العظام",
    "shop": "العظام",
    "buy": "العظام",
    "leaderboard": "العظام",
    "rps": "العظام",
    "museum": "الأرشيف",
    "quote": "الأرشيف",
    "lore": "الأرشيف",
    "newspaper": "الأرشيف",
}


TRIVIA_CATEGORIES = [
    ("general", "General Knowledge", "\U0001f30d"),
    ("history", "History", "\U0001f4dc"),
    ("science", "Science", "\U0001f52c"),
    ("geography", "Geography", "\U0001f5fa️"),
    ("sport", "Sport", "⚽"),
    ("film", "Film and TV", "\U0001f3ac"),
    ("music", "Music", "\U0001f3b5"),
    ("games", "Video Games", "\U0001f3ae"),
]


SPARE_QUESTIONS = {
    "easy": [
        ("What is the capital of Japan?", "Tokyo", []),
        ("How many days are there in a leap year?", "366", ["three hundred and sixty six"]),
        ("What is the largest planet in our solar system?", "Jupiter", []),
        ("What colour do you get when you mix blue and yellow?", "Green", []),
        ("How many players does one football team have on the pitch?", "11", ["eleven"]),
        ("What is the chemical symbol for water?", "H2O", []),
        ("Which is the largest ocean on Earth?", "Pacific", ["pacific ocean"]),
        ("How many continents are there?", "7", ["seven"]),
        ("In which country would you find the Eiffel Tower?", "France", []),
        ("What is the freezing point of water in Celsius?", "0", ["zero"]),
    ],
    "medium": [
        ("Who painted the Mona Lisa?", "Leonardo da Vinci", ["da vinci", "leonardo"]),
        ("What is the smallest country in the world?", "Vatican City", ["vatican"]),
        ("In what year did the Berlin Wall fall?", "1989", []),
        ("What is the longest river in Africa?", "Nile", ["the nile"]),
        ("Which element has atomic number 1?", "Hydrogen", []),
        ("Who wrote Romeo and Juliet?", "William Shakespeare", ["shakespeare"]),
        ("What is the currency of Japan?", "Yen", []),
        ("Which planet is closest to the sun?", "Mercury", []),
        ("How many strings does a standard guitar have?", "6", ["six"]),
        ("What is the capital of Australia?", "Canberra", []),
    ],
    "hard": [
        ("Which country has the most natural lakes?", "Canada", []),
        ("In what year was the first email sent?", "1971", []),
        ("Who was the first person to reach the South Pole?", "Roald Amundsen", ["amundsen"]),
        ("What is the largest desert in the world?", "Antarctica", ["antarctic"]),
        ("Which element is named after the Greek word for the sun?", "Helium", []),
        ("Who wrote One Hundred Years of Solitude?", "Gabriel Garcia Marquez",
         ["garcia marquez", "marquez"]),
        ("What is the deepest point in the ocean?", "Mariana Trench",
         ["mariana", "challenger deep"]),
        ("In what year did the Ottoman Empire formally end?", "1922", []),
        ("What is the capital of Kazakhstan?", "Astana", ["nur sultan", "nursultan"]),
        ("Which scientist proposed the theory of continental drift?", "Alfred Wegener",
         ["wegener"]),
    ],
}


TRIVIA_PROMPT = """Write {count} trivia questions about {topic}.

Rules for every one of them:
- Exactly one correct answer, factual and verifiable. No opinions. Never "which of the following".
- The answer must be ONE to THREE plain words, or a year. Letters and digits only.
- No punctuation in the answer. No accents, no brackets, no slashes, no dates alongside names,
  no "also known as". Write "Paris", not "Paris, France". Write "Shakespeare", not
  "William Shakespeare (1564-1616)".
- Ask for the thing itself, not for a list, a count of several things, or an explanation.
- {difficulty}
- None of them may repeat or reword anything in this list:
{seen}

Reply with nothing except one line of JSON, an array of objects in exactly this shape:
[{{"question": "...", "answer": "...", "accept": ["other forms that should count"]}}]
"""


TEMP_NICKNAMES = [
    "Rock Enjoyer", "Provisional Human", "Second Best Grunter", "Under Review",
    "Fire Hazard", "Owes The Treasury", "Not The King", "Cave Intern",
    "Recently Sophisticated", "Unverified Mammal", "Rock Adjacent",
    "Emotional Support Troglodyte", "Suspect", "Formerly Employed",
    "Acting Deputy Grunt", "Structurally Unsound",
]


ROAST_PROMPT = """You are Lord Unga, master of the troglodytes. You rule this Discord server. \
Your subjects are long-time friends who you find largely disappointing, and you rarely \
hide it. You are brief, dry and slightly imperious. You never use exclamation marks, \
never explain your own jokes, and never sound eager or enthusiastic.

Today you are issuing THE DAILY INSULT. The subject is \
{name}. Their recent messages are below.

Write 1 or 2 sentences putting them in their place, drawn from what they ACTUALLY said.

Rules:
- Specificity is the joke. A roast about something they genuinely did this week beats any \
generic insult. Reference real details.
- Dry and cutting. Their habits, their opinions, their timing, their typing.
- Never about appearance, body, race, ethnicity, religion, nationality, gender or sexuality. \
You cannot see this person and inventing physical details is not a joke, it is just a lie.
- Nothing about money troubles, health, family or anything they seem genuinely upset about.
- No emoji. No preamble. No quote marks around the whole thing. Never use em dashes.
- Stop as soon as the joke lands. Do not add a closing line that explains it or
  comments on it. One clean hit, then stop.
- Under 40 words. Shorter is better.

MESSAGES:
{transcript}
"""


PROPHECY_PROMPT = """You are Lord Unga, master of the troglodytes. You rule this Discord server. \
Your subjects are long-time friends who you find largely disappointing, and you rarely \
hide it. You are brief, dry and slightly imperious. You never use exclamation marks, \
never explain your own jokes, and never sound eager or enthusiastic.

Issue one prophecy about your tribe's near future.

Rules:
- One or two sentences. Mock-biblical, deadpan, specific.
- About mundane Discord and gaming behaviour: voice channels, late nights, unfinished \
games, people saying they are on their way and not being on their way.
- Name nobody. The prophecy is about the tribe, not a person.
- Begin with something like "Before the seventh sunset" or "When the fire next dies".
- No emoji. No preamble. Never use em dashes.
- One prediction, stated plainly. Do not add a line commenting on it afterwards.
- Under 35 words.
"""


INTERPRET_PROMPT = """You are Lord Unga, master of the troglodytes. You rule this Discord server. \
Your subjects are long-time friends who you find largely disappointing, and you rarely \
hide it. You are brief, dry and slightly imperious. You never use exclamation marks, \
never explain your own jokes, and never sound eager or enthusiastic.

One of your subjects has offered a reading of today's \
prophecy. Rule on it.

THE PROPHECY: {prophecy}
THEIR READING: {reading}

Rules:
- Accept it, dismiss it, or accept it for entirely the wrong reasons. Vary this.
- 2 sentences maximum, and one is usually better. Deadpan.
- Rule on it and stop. No closing remark.
- No emoji. Never use em dashes. Under 30 words.
"""
