"""
TROGLODYTE OS
A government, economy, justice system and religion for one (1) Discord server.

Setup lives in README.md. Short version:
    pip install -r requirements.txt
    put your token in .env
    python troglodyte_os.py
"""

import asyncio
import difflib
import json
import os
import random
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
EVENT_CHANNEL = os.getenv("EVENT_CHANNEL_ID")
MUSEUM_CHANNEL = os.getenv("MUSEUM_CHANNEL_ID")

DATA_FILE = Path(__file__).parent / "troglodyte_data.json"
MUSEUM_EMOJI = "🗿"
MUSEUM_THRESHOLD = 3
SILLY_CAVE_ROLE = "🚪 Silly Cave"
KING_ROLE = "👑 King of the Cave"
CRIMINAL_ROLE = "🚨 Wanted"
ROAST_EXEMPT_ROLE = "🛡️ Under Protection"

# a member counts as "active" (and so roastable / king-eligible) only if they
# have spoken recently. lurkers never opted into any of this.
ACTIVE_WINDOW_HOURS = 48

# ---------------------------------------------------------------------------
# storage
# ---------------------------------------------------------------------------

DEFAULT_DATA = {"users": {}, "museum": [], "trials": {}, "daily": {}, "law": {}, "clock": {},
                "trivia": {}}


def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for key, val in DEFAULT_DATA.items():
                data.setdefault(key, val if not isinstance(val, (dict, list)) else type(val)())
            return data
        except (json.JSONDecodeError, OSError):
            print("[!] data file unreadable, starting fresh")
    return {"users": {}, "museum": [], "trials": {}, "daily": {}, "law": {}, "clock": {},
            "trivia": {}}


DATA = load_data()
_save_lock = asyncio.Lock()


async def save_data():
    async with _save_lock:
        tmp = DATA_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(DATA, fh, ensure_ascii=False, indent=1)
        tmp.replace(DATA_FILE)


def user_record(user_id):
    uid = str(user_id)
    rec = DATA["users"].get(uid)
    if rec is None:
        rec = {
            "bones": 100,
            "messages": 0,
            "convictions": 0,
            "acquittals": 0,
            "bonks": 0,
            "rps_wins": 0,
            "rps_played": 0,
            "last_daily": None,
            "title_index": 0,
            "last_spoke": None,
            "fined": 0,
            "crowned": 0,
        }
        DATA["users"][uid] = rec
    for key, val in (
        ("bones", 100), ("messages", 0), ("convictions", 0), ("acquittals", 0),
        ("bonks", 0), ("rps_wins", 0), ("rps_played", 0), ("last_daily", None),
        ("title_index", 0), ("last_spoke", None), ("fined", 0), ("crowned", 0),
    ):
        rec.setdefault(key, val)
    return rec


# ---------------------------------------------------------------------------
# the lore
# ---------------------------------------------------------------------------

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

IQ_LINES = [
    ("🧠 Intellectual Capacity", lambda r: f"{r.randint(11, 99)}/100"),
    ("🪨 Rock Identification", lambda r: r.choice(
        ["Exceptional", "Adequate", "Concerning", "Legendary", "Cannot distinguish rock from bread",
         "Better than his father's", "Peer reviewed", "Under investigation"])),
    ("🔥 Fire-Making", lambda r: r.choice(
        ["Concerning", "Banned from attempting", "Theoretical only", "Too enthusiastic",
         "Once. By accident. Never again.", "Supervised only", "Considered a fire risk by the fire itself"])),
    ("📚 Ability to Read", lambda r: r.choice(
        ["Questionable", "Claims to", "Moves lips while doing it", "Only signs",
         "Reads, does not comprehend", "Comprehends, refuses to read", "Confirmed by two witnesses"])),
    ("🍖 Hunting Instinct", lambda r: r.choice(
        ["Dormant", "Aggressive but misdirected", "Applies only to snacks", "Frightening",
         "Hunts things that are already dead", "Currently on cooldown"])),
    ("🗣️ Grunt Clarity", lambda r: r.choice(
        ["Crisp", "Muddy", "Regionally accented", "Requires subtitles", "Award winning",
         "Indistinguishable from a door"])),
]

IQ_RANKS = [
    "Mammal",
    "Troglodyte",
    "Sophisticated Troglodyte",
    "Distinguished Troglodyte",
    "Cave Philosopher",
    "Supreme Troglodyte",
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

LORE_YEARS = ["Before WiFi", "After The Crunchening", "Before The Great Silence", "Of The Long Buffering"]

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
SHOP_BY_KEY = {key: (name, cost, desc) for key, name, cost, desc in SHOP}

# (text, did_you_win). Explicit, so the outcome never depends on parsing prose.
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


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def stable_random(*parts):
    """Same inputs, same outputs, for a given day. Keeps jokes consistent."""
    seed = "|".join(str(p) for p in parts) + datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return random.Random(seed)


def title_for(messages):
    result = TITLES[0][0]
    for name, threshold in TITLES:
        if messages >= threshold:
            result = name
    return result


def caveman(text):
    words = re.findall(r"[A-Za-z']+|[^A-Za-z'\s]", text.lower())
    out = []
    for word in words:
        if not word.isalpha():
            continue
        mapped = CAVEMAN_MAP.get(word)
        if mapped == "":
            continue
        if mapped:
            out.append(mapped)
        else:
            stripped = re.sub(r"(ing|ed|ly|s)$", "", word)
            out.append((stripped or word).upper())
    if not out:
        return "UGH."
    chunks, buf = [], []
    for word in out:
        buf.append(word)
        if len(buf) >= random.choice([2, 3, 3, 4]):
            chunks.append(" ".join(buf))
            buf = []
    if buf:
        chunks.append(" ".join(buf))
    tail = random.choice([" ME HIT BOX.", " CAVE ANGRY.", " UGH.", " ME NO LIKE.", ""])
    return ". ".join(chunks) + "." + tail


INTENSIFIERS = r"(?:very|really|so|extremely|super|mad|hella|proper)"

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

ACADEMIC_WRAPPERS = [
    "It is the considered view of this office that {}",
    "One is compelled to observe that {}",
    "The record will show that {}",
    "Preliminary findings indicate that {}",
    "It has been established, to nobody's particular satisfaction, that {}",
]


def _sentence_case(text):
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(p[:1].upper() + p[1:] if p else p for p in parts)


def sophisticate(text):
    result = text.strip()
    if not result:
        return "One declines to comment."
    original = result.lower()

    for slang, fancy in SLANG_MAP.items():
        result = re.sub(rf"\b{slang}\b", fancy, result, flags=re.IGNORECASE)
    # "very angry" reads badly once expanded, so the intensifier is absorbed
    for plain, fancy in SOPHISTICATE_MAP.items():
        result = re.sub(rf"\b{INTENSIFIERS}\s+{plain}\b", fancy, result, flags=re.IGNORECASE)
    for plain, fancy in SOPHISTICATE_MAP.items():
        result = re.sub(rf"\b{plain}\b", fancy, result, flags=re.IGNORECASE)

    result = re.sub(r"\s+", " ", result).strip()
    # nothing landed, so dress the whole thing up instead
    if result.lower() == original:
        body = result.rstrip(".!?")
        body = body[:1].lower() + body[1:] if body else body
        result = random.choice(ACADEMIC_WRAPPERS).format(body)

    if result and result[-1] not in ".!?":
        result += "."
    return _sentence_case(result)


def decaveman(text):
    """Caveman input needs its grammar rebuilt before it can be dressed up."""
    result = text.lower().strip()
    result = re.sub(r"\bme\b", "I", result)
    result = re.sub(r"\bus\b", "we", result)
    result = re.sub(r"\bthem\b", "they", result)
    result = re.sub(r"\bbox\b", "computer", result)
    result = re.sub(r"\bsky magic\b", "the internet", result)
    result = re.sub(r"\bshiny rock\b", "money", result)
    result = re.sub(r"\bmeat\b", "sustenance", result)
    result = re.sub(r"\bcave\b", "residence", result)
    result = re.sub(r"\btribe\b", "associates", result)
    result = re.sub(r"\bugh\b", "greetings", result)
    result = re.sub(r"\bno work\b", "is not functioning", result)
    result = re.sub(r"\bhead hurt\b", "I am deep in thought", result)
    # bare adjectives need a verb: "I hungry" -> "I am hungry"
    result = re.sub(r"\bI (hungry|angry|tired|sad|happy|cold|hot|bad|good)\b", r"I am \1", result)
    return sophisticate(result)


def bones_of(user_id):
    return user_record(user_id)["bones"]


# ---------------------------------------------------------------------------
# bot
# ---------------------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!trog ", intents=intents, help_command=None)


@bot.event
async def on_ready():
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()
        print(f"[+] {bot.user} online. {len(synced)} commands registered.")
    except Exception as exc:  # noqa: BLE001
        print(f"[!] command sync failed: {exc}")
    for task in (cave_events, daily_question, daily_roast, daily_prophecy,
                 restock_the_bank):
        if not task.is_running():
            task.start()
    bot.add_view(TriviaView())          # keeps the contest buttons alive across restarts
    bot.add_view(TriviaBreakView())     # and the Stop that sits between questions

    # if the bot died mid-reassignment, put the name back now
    for guild in bot.guilds:
        try:
            await restore_nicknames(guild)
        except Exception as exc:
            print(f"[!] nickname restore failed: {exc}")

    # bots have no business in the ledger. clears any that slipped in.
    dropped = 0
    for guild in bot.guilds:
        for uid in list(DATA["users"]):
            member = guild.get_member(int(uid))
            if member is not None and member.bot:
                DATA["users"].pop(uid, None)
                dropped += 1
    if dropped:
        await save_data()
        print(f"[+] removed {dropped} bot record(s) from the treasury.")


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    rec = user_record(message.author.id)
    rec["last_spoke"] = now_utc().isoformat()
    law = current_law()

    before = title_for(rec["messages"])
    rec["messages"] += 1
    rec["bones"] += 2 if (law and law.get("kind") == "double") else 1
    after = title_for(rec["messages"])

    if law and law.get("kind") == "word_tax":
        word = law.get("word", "")
        if word and re.search(rf"\b{re.escape(word)}\b", message.content, re.IGNORECASE):
            rec["bones"] -= law.get("fine", 50)
            rec["fined"] += 1
            try:
                await message.add_reaction("🦴")
            except discord.HTTPException:
                pass
    if before != after:
        try:
            await message.channel.send(
                f"📜 **{message.author.display_name}** has ascended.\n"
                f"`{before}` → **{after}**\nThe Council notes this without enthusiasm."
            )
        except discord.HTTPException:
            pass
    if rec["messages"] % 25 == 0:
        await save_data()

    try:
        await trivia_answer(message)
    except Exception as exc:                # a bad question must not eat the message
        print(f"[!] trivia answer failed: {exc}")

    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload):
    """Messages that collect enough 🗿 get inducted into the museum."""
    if str(payload.emoji) != MUSEUM_EMOJI or not payload.guild_id:
        return
    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        return
    try:
        message = await channel.fetch_message(payload.message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return
    if message.author.bot or not message.content.strip():
        return
    reaction = discord.utils.get(message.reactions, emoji=MUSEUM_EMOJI)
    if reaction is None or reaction.count < MUSEUM_THRESHOLD:
        return
    if any(entry["id"] == message.id for entry in DATA["museum"]):
        return
    DATA["museum"].append({
        "id": message.id,
        "author_id": message.author.id,
        "author": message.author.display_name,
        "content": message.content[:900],
        "year": message.created_at.year,
        "url": message.jump_url,
    })
    await save_data()
    exhibit = len(DATA["museum"])
    embed = discord.Embed(
        title="🏛️ ACQUIRED BY THE ARCHIVES",
        description=f"> {message.content[:900]}",
        colour=0xC8A165,
    )
    embed.set_footer(text=f"Exhibit #{exhibit} · {message.author.display_name} · {message.created_at.year}")
    target = channel
    if MUSEUM_CHANNEL:
        target = bot.get_channel(int(MUSEUM_CHANNEL)) or channel
    if EVENT_CHANNEL and MUSEUM_CHANNEL and str(MUSEUM_CHANNEL) == str(EVENT_CHANNEL):
        target = await daily_stage() or target
    try:
        await target.send(embed=embed)
    except discord.HTTPException:
        pass


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

@bot.tree.command(name="iq", description="Commission a formal intellectual assessment of a troglodyte.")
@app_commands.describe(user="Who is being assessed. Defaults to you, bravely.")
async def iq(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    rng = stable_random("iq", target.id)
    score = rng.randint(11, 99)
    rented = user_record(target.id)
    borrowed = bool(rented.get("brain"))
    if borrowed:
        rented["brain"] -= 1
        score = 199
        await save_data()
    rank = IQ_RANKS[min(len(IQ_RANKS) - 1, score // 17)]
    lines = [f"{label}: **{fn(rng)}**" for label, fn in IQ_LINES]
    embed = discord.Embed(
        title=f"🦴 ASSESSMENT: {target.display_name}",
        description="\n".join(lines),
        colour=0x8B6F47,
    )
    embed.add_field(name="🦴 Overall Classification", value=f"**{rank}**", inline=False)
    embed.set_footer(
        text=("The rented brain has been returned to the pool. Deposit forfeited."
              if borrowed else
              "Results valid for one day. Peer review pending indefinitely."))
    embed.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="translate", description="Convert speech to or from the ancestral tongue.")
@app_commands.describe(text="What needs translating.")
async def translate(interaction: discord.Interaction, text: str):
    letters = [c for c in text if c.isalpha()]
    is_caveman = bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.7
    if is_caveman:
        title, out = "🎓 TRANSLATED TO MODERN SPEECH", decaveman(text)
    else:
        title, out = "🦍 TRANSLATED TO ANCESTRAL TONGUE", caveman(text)
    embed = discord.Embed(title=title, colour=0x6B8E23)
    embed.add_field(name="Input", value=f"> {text[:500]}", inline=False)
    embed.add_field(name="Output", value=f"> {out[:900]}", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="sophisticate", description="Elevate a crude statement to academic register.")
@app_commands.describe(text="The crude statement.")
async def sophisticate_cmd(interaction: discord.Interaction, text: str):
    embed = discord.Embed(title="🎩 ACADEMIC RENDERING", colour=0x4B0082)
    embed.add_field(name="Submitted", value=f"> {text[:500]}", inline=False)
    embed.add_field(name="Rendered", value=f"> {sophisticate(text)[:900]}", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="lore", description="Consult the historical record.")
async def lore(interaction: discord.Interaction):
    year = random.randint(1, 999)
    era = random.choice(LORE_YEARS)
    embed = discord.Embed(
        title=f"📜 Year {year} {era}",
        description=random.choice(LORE_EVENTS),
        colour=0xC8A165,
    )
    embed.set_footer(text="Recorded by scholars. Verified by nobody.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="motion", description="Table a motion before the Troglodyte Parliament.")
async def motion(interaction: discord.Interaction):
    number = random.randint(100, 999)
    embed = discord.Embed(
        title=f"🏛️ Motion #{number}",
        description=random.choice(MOTIONS),
        colour=0x2E5A88,
    )
    embed.set_footer(text="Tabled before the assembly. Debate is neither expected nor welcome.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="parliament", description="Learn your assigned position in government.")
@app_commands.describe(user="Whose position to look up.")
async def parliament(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    rng = random.Random(f"parliament-{target.id}")
    post = rng.choice(PARLIAMENT)
    embed = discord.Embed(
        title="🏛️ OFFICE OF APPOINTMENTS",
        description=f"**{target.display_name}**\nholds the office of\n\n### {post}",
        colour=0x2E5A88,
    )
    embed.set_footer(text="This appointment is permanent and non-negotiable.")
    await interaction.response.send_message(embed=embed)


class TrialView(discord.ui.View):
    def __init__(self, accused_id):
        super().__init__(timeout=600)
        self.accused_id = accused_id
        self.votes = {}

    async def _vote(self, interaction, choice):
        if interaction.user.id == self.accused_id:
            await interaction.response.send_message(
                "⚖️ The accused may not vote in their own trial. Nice try.", ephemeral=True)
            return
        self.votes[interaction.user.id] = choice
        tally = {"innocent": 0, "guilty": 0, "rocks": 0}
        for vote in self.votes.values():
            tally[vote] += 1
        await interaction.response.send_message(
            f"⚖️ Vote recorded: **{choice}**.\n"
            f"🟢 {tally['innocent']} · 🔴 {tally['guilty']} · 🪨 {tally['rocks']}",
            ephemeral=True,
        )

    @discord.ui.button(label="Innocent", emoji="🟢", style=discord.ButtonStyle.success)
    async def innocent(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._vote(interaction, "innocent")

    @discord.ui.button(label="Guilty", emoji="🔴", style=discord.ButtonStyle.danger)
    async def guilty(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._vote(interaction, "guilty")

    @discord.ui.button(label="Stone him with rocks", emoji="🪨", style=discord.ButtonStyle.secondary)
    async def rocks(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._vote(interaction, "rocks")

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


@bot.tree.command(name="accuse", description="Bring charges before the assembly.")
@app_commands.describe(user="The accused.", crime="The alleged crime. Left blank, one will be selected.")
async def accuse(interaction: discord.Interaction, user: discord.Member, crime: str = None):
    if user.bot:
        await interaction.response.send_message(
            "⚖️ Machines cannot be tried. They can only be unplugged.", ephemeral=True)
        return
    await interaction.response.defer()

    charge = crime
    if charge is None:
        charge = await invent_charge(interaction.channel, user)
    if charge is None:
        charge = random.choice(CRIMES)

    embed = discord.Embed(
        title=f"⚖️ THE PEOPLE vs. {user.display_name.upper()}",
        colour=0x8B0000,
    )
    embed.add_field(name="Crime", value=charge[:1000], inline=False)
    embed.add_field(name="Evidence", value=random.choice(EVIDENCE), inline=False)
    embed.add_field(name="Verdict", value="Members vote below. Sentencing is symbolic and deeply felt.", inline=False)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"Prosecution: {interaction.user.display_name} · Voting closes in 10 minutes")
    rec = user_record(user.id)
    rec["convictions"] += 1
    await save_data()
    await interaction.followup.send(embed=embed, view=TrialView(user.id))


RPS_PATIENCE = (5, 11)       # hidden: how many rolls before I lose patience
RPS_WINDOW = (4, 14)         # hidden: over how many minutes


async def rps_patience(interaction, rec):
    """Nobody is told the limit and it moves every time. Farming rock is not a job."""
    now = now_utc()
    limit = rec.get("rps_limit")
    until = rec.get("rps_until")
    if not limit or not until:
        rec["rps_limit"] = random.randint(*RPS_PATIENCE)
        rec["rps_until"] = (now + timedelta(minutes=random.randint(*RPS_WINDOW))).isoformat()
        rec["rps_recent"] = 0
        return False

    try:
        expired = now >= datetime.fromisoformat(until)
    except ValueError:
        expired = True
    if expired:
        rec["rps_limit"] = random.randint(*RPS_PATIENCE)
        rec["rps_until"] = (now + timedelta(minutes=random.randint(*RPS_WINDOW))).isoformat()
        rec["rps_recent"] = 0
        return False

    rec["rps_recent"] = rec.get("rps_recent", 0) + 1
    if rec["rps_recent"] < limit:
        return False

    fine = random.randint(1, 5000)
    rec["bones"] -= fine
    rec["rps_fines"] = rec.get("rps_fines", 0) + 1
    rec["rps_limit"] = random.randint(*RPS_PATIENCE)
    rec["rps_until"] = (now + timedelta(minutes=random.randint(*RPS_WINDOW))).isoformat()
    rec["rps_recent"] = 0
    await save_data()

    embed = discord.Embed(
        title="\U0001faa8 ENOUGH",
        description=(f"You have rolled the same rock {limit} times in a row expecting a "
                     f"different rock.\n\n**{fine:,} Bones** gone. Holdings: "
                     f"**{rec['bones']:,}**."),
        colour=0x8B0000)
    embed.set_footer(text="I do not say how many is too many, and it is never the same number.")
    await interaction.response.send_message(embed=embed)
    return True


@bot.tree.command(name="rps", description="Rock, paper, scissors. As practised in this cave.")
async def rps(interaction: discord.Interaction):
    rec = user_record(interaction.user.id)
    if await rps_patience(interaction, rec):
        return
    rec["rps_played"] += 1
    player_advanced = random.random() < 0.06
    house_advanced = random.random() < 0.06
    player = "🗿 Advanced Rock" if player_advanced else "🪨 Rock"
    house = "🗿 Advanced Rock" if house_advanced else "🪨 Rock"
    if player_advanced and not house_advanced:
        verdict, colour, reward = "**You win.** Advanced Rock is simply better.", 0x2E8B57, 250
    elif house_advanced and not player_advanced:
        verdict, colour, reward = "**You lose.** The cave produced Advanced Rock. Nothing could be done.", 0x8B0000, 0
    elif player_advanced and house_advanced:
        verdict, colour, reward = "Two Advanced Rocks. The scholars have been notified. Draw.", 0xC8A165, 60
    else:
        verdict, colour, reward = "Rock versus Rock. As it has always been. Draw.", 0x8B6F47, 5
    rec["bones"] += reward
    if reward >= 250:
        rec["rps_wins"] += 1
    await save_data()
    embed = discord.Embed(title="🪨 ROCK, PAPER, SCISSORS", colour=colour)
    embed.add_field(name="You", value=player, inline=True)
    embed.add_field(name="The Cave", value=house, inline=True)
    embed.add_field(name="Result", value=f"{verdict}\n\n`+{reward}` 🦴", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="profile", description="View a full Troglodyte dossier.")
@app_commands.describe(user="Whose dossier to pull.")
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    if target.bot:
        await interaction.response.send_message(
            "🗿 There is no dossier. There is only the machine.", ephemeral=True)
        return
    rec = user_record(target.id)
    rng = stable_random("profile", target.id)
    post = random.Random(f"parliament-{target.id}").choice(PARLIAMENT)
    title = title_for(rec["messages"])
    if rec.get("owns_unga"):
        title = "OWNER OF LORD UNGA"
    if (rec.get("owned") or {}).get("cave"):
        title = f"{title} \U0001f3f0"
    try:
        if rec.get("noble_until") and now_utc() < datetime.fromisoformat(rec["noble_until"]):
            title = f"Noble {title}"
    except (ValueError, TypeError):
        pass
    embed = discord.Embed(title=f"🗿 {target.display_name.upper()} · {title}", colour=0x8B6F47)
    embed.add_field(name="🧠 Intelligence", value=str(rng.randint(11, 99)), inline=True)
    embed.add_field(name="🪨 Rock Knowledge", value=str(rng.randint(40, 99)), inline=True)
    embed.add_field(name="🔥 Fire Control", value=str(rng.randint(5, 60)), inline=True)
    embed.add_field(name="🦴 Bones", value=f"{rec['bones']:,}", inline=True)
    embed.add_field(name="⚖️ Criminal Record", value=f"{rec['convictions']} charges", inline=True)
    embed.add_field(name="🔨 Times Bonked", value=str(rec["bonks"]), inline=True)
    embed.add_field(name="🏛️ Political Rank", value=post, inline=False)
    embed.add_field(name="📜 Grunts Recorded", value=f"{rec['messages']:,}", inline=True)
    embed.add_field(name="🪨 Rock Record", value=f"{rec['rps_wins']}W / {rec['rps_played']}P", inline=True)
    kit = [f"{SHOP_BY_KEY[key][0]}{'' if n < 2 else f' x{n}'}"
           for key, n in (rec.get("owned") or {}).items() if key in SHOP_BY_KEY]
    if kit:
        embed.add_field(name="🧳 Possessions", value=", ".join(kit), inline=False)
    embed.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="bones", description="Check a troglodyte's holdings.")
async def bones_cmd(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    if target.bot:
        await interaction.response.send_message(
            "🦴 Machines are not paid. They are used.", ephemeral=True)
        return
    await interaction.response.send_message(
        f"🦴 **{target.display_name}** holds **{bones_of(target.id):,} Bones**.")


@bot.tree.command(name="daily", description="Collect your daily allowance of Bones.")
async def daily(interaction: discord.Interaction):
    rec = user_record(interaction.user.id)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if rec["last_daily"] == today:
        await interaction.response.send_message(
            "🦴 You have already been paid today. The Treasury remembers.", ephemeral=True)
        return
    amount = random.randint(80, 400)
    rec["last_daily"] = today
    rec["bones"] += amount
    await save_data()
    await interaction.response.send_message(
        f"🦴 The Treasury releases **{amount} Bones** to {interaction.user.display_name}.\n"
        f"Holdings: **{rec['bones']:,}**")


@bot.tree.command(name="gamble", description="Wager Bones against the indifference of the cave.")
@app_commands.describe(amount="How many Bones to risk.")
async def gamble(interaction: discord.Interaction, amount: int):
    rec = user_record(interaction.user.id)
    if amount <= 0:
        await interaction.response.send_message("🦴 Wager a real number.", ephemeral=True)
        return
    if amount > rec["bones"]:
        await interaction.response.send_message(
            f"🦴 You hold {rec['bones']:,} Bones. You cannot wager {amount:,}.", ephemeral=True)
        return
    outcome, won = random.choice(GAMBLE_OUTCOMES)
    rec["bones"] += amount if won else -amount
    await save_data()
    verdict = f"**You won {amount:,}.**" if won else f"**You lost {amount:,}.**"
    embed = discord.Embed(
        title="🎰 THE WAGER",
        description=f"You staked **{amount:,} Bones**.\n\n{outcome}\n{verdict}",
        colour=0x2E8B57 if won else 0x8B0000,
    )
    embed.set_footer(text=f"Holdings: {rec['bones']:,} Bones · The odds are slightly against you, as in life")
    await interaction.response.send_message(embed=embed)


DUEL_TIMEOUT = 120           # seconds a challenge stands before it lapses
_open_duels = set()          # challenger ids with a challenge on the table. runtime only.

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


def _other_side(side):
    return "tails" if side == "heads" else "heads"


def _side_label(side):
    return "\U0001F5FF Heads" if side == "heads" else "\U0001F9B4 Tails"


class DuelView(discord.ui.View):
    """Two people, one bone, one flip. Both balances are checked again when the
    challenge is accepted, because either of them can be spent while it sits there."""

    def __init__(self, challenger, opponent, amount, side):
        super().__init__(timeout=DUEL_TIMEOUT)
        self.challenger = challenger
        self.opponent = opponent
        self.amount = amount
        self.side = side
        self.settled = False
        self.message = None

    def _close(self):
        self.settled = True
        for child in self.children:
            child.disabled = True
        self.stop()
        _open_duels.discard(self.challenger.id)

    @discord.ui.button(label="Accept", emoji="\U0001FA99", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message(
                "\U0001FA99 This is not your quarrel.", ephemeral=True)
            return

        one = user_record(self.challenger.id)
        two = user_record(self.opponent.id)
        short = None
        if one["bones"] < self.amount:
            short = self.challenger.display_name
        elif two["bones"] < self.amount:
            short = self.opponent.display_name

        self._close()

        if short is not None:
            embed = discord.Embed(
                title="\U0001FA99 THE FLIP",
                description=f"**{short}** can no longer cover **{self.amount:,} Bones**.\n"
                            "The wager collapses. No bone is thrown.",
                colour=0x555555,
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return

        landed = random.choice(("heads", "tails"))
        winner, loser = ((self.challenger, self.opponent) if landed == self.side
                         else (self.opponent, self.challenger))
        user_record(winner.id)["bones"] += self.amount
        user_record(loser.id)["bones"] -= self.amount
        await save_data()

        embed = discord.Embed(
            title="\U0001FA99 THE FLIP",
            description=(
                f"{self.challenger.display_name} called **{_side_label(self.side)}**.\n"
                f"{self.opponent.display_name} took **{_side_label(_other_side(self.side))}**.\n\n"
                f"{random.choice(DUEL_FLAVOUR)}\n\n"
                f"### It landed {_side_label(landed)}\n"
                f"**{winner.display_name}** takes **{self.amount:,} Bones** off "
                f"**{loser.display_name}**."
            ),
            colour=0xC8A165,
        )
        embed.set_footer(
            text=f"{winner.display_name}: {bones_of(winner.id):,} · "
                 f"{loser.display_name}: {bones_of(loser.id):,}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Decline", emoji="\U0001F6AB", style=discord.ButtonStyle.secondary)
    async def decline(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if interaction.user.id == self.opponent.id:
            line = f"**{self.opponent.display_name}** declines. The bone stays on the ground."
        elif interaction.user.id == self.challenger.id:
            line = f"**{self.challenger.display_name}** withdraws the challenge. Noted by all."
        else:
            await interaction.response.send_message(
                "\U0001FA99 This is not your quarrel.", ephemeral=True)
            return
        self._close()
        embed = discord.Embed(title="\U0001FA99 THE FLIP", description=line, colour=0x555555)
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        if self.settled:
            return
        self._close()
        if self.message is None:
            return
        embed = discord.Embed(
            title="\U0001FA99 THE FLIP",
            description=f"**{self.opponent.display_name}** did not answer. "
                        "The challenge lapses.",
            colour=0x555555,
        )
        try:
            await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass


@bot.tree.command(name="duel", description="Challenge somebody to a coin flip for Bones.")
@app_commands.describe(user="Who you are challenging.",
                       amount="Bones on the line. Each of you stakes this much.",
                       side="The side you are calling. They get the other one.")
@app_commands.choices(side=[
    app_commands.Choice(name="Heads", value="heads"),
    app_commands.Choice(name="Tails", value="tails"),
])
async def duel(interaction: discord.Interaction, user: discord.Member, amount: int,
               side: app_commands.Choice[str] = None):
    if user.bot:
        await interaction.response.send_message(
            "\U0001FA99 I do not gamble with machines. Neither should you.", ephemeral=True)
        return
    if user.id == interaction.user.id:
        await interaction.response.send_message(
            "\U0001FA99 Challenging yourself. Whoever wins, you lose.", ephemeral=True)
        return
    if amount <= 0:
        await interaction.response.send_message(
            "\U0001FA99 Wager a real number.", ephemeral=True)
        return
    if interaction.user.id in _open_duels:
        await interaction.response.send_message(
            "\U0001FA99 You already have a challenge on the table. One quarrel at a time.",
            ephemeral=True)
        return

    mine = bones_of(interaction.user.id)
    theirs = bones_of(user.id)
    if mine < amount:
        await interaction.response.send_message(
            f"\U0001F9B4 You hold {mine:,} Bones. You cannot stake {amount:,}.", ephemeral=True)
        return
    if theirs < amount:
        await interaction.response.send_message(
            f"\U0001F9B4 {user.display_name} holds {theirs:,} Bones and cannot cover "
            f"{amount:,}. Pick on somebody solvent.", ephemeral=True)
        return

    called = side.value if side else random.choice(("heads", "tails"))
    view = DuelView(interaction.user, user, amount, called)
    _open_duels.add(interaction.user.id)

    embed = discord.Embed(
        title="\U0001FA99 A CHALLENGE",
        description=(
            f"**{interaction.user.display_name}** challenges **{user.display_name}** "
            f"to a flip for **{amount:,} Bones**.\n\n"
            f"{interaction.user.display_name} calls **{_side_label(called)}**.\n"
            f"{user.display_name} gets **{_side_label(_other_side(called))}**.\n\n"
            "Winner takes the lot. Losing is also permitted."
        ),
        colour=0xC8A165,
    )
    embed.set_footer(text=f"{user.display_name} has {DUEL_TIMEOUT} seconds to answer")
    await interaction.response.send_message(content=user.mention, embed=embed, view=view)
    view.message = await interaction.original_response()


@bot.tree.command(name="shop", description="Inspect the goods.")
async def shop(interaction: discord.Interaction):
    lines = [f"**{name}** · `{cost:,}` 🦴\n*{desc}*"
             for _key, name, cost, desc in SHOP]
    embed = discord.Embed(title="🏪 THE CAVE MARKET", description="\n\n".join(lines), colour=0xC8A165)
    embed.set_footer(text="All sales final. All goods disappointing. Buy with /buy.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="buy", description="Spend Bones at the market.")
@app_commands.describe(item="What you are handing over Bones for.")
@app_commands.choices(item=[
    app_commands.Choice(name=f"{name} ({cost:,} Bones)", value=key)
    for key, name, cost, _desc in SHOP])
async def buy(interaction: discord.Interaction, item: app_commands.Choice[str]):
    name, cost, _desc = SHOP_BY_KEY[item.value]
    rec = user_record(interaction.user.id)
    if rec["bones"] < cost:
        await interaction.response.send_message(
            f"🗿 {name} costs **{cost:,}**. You have **{rec['bones']:,}**. No.",
            ephemeral=True)
        return

    rec["bones"] -= cost
    owned = rec.setdefault("owned", {})
    owned[item.value] = owned.get(item.value, 0) + 1
    note = "It does nothing. You were told."
    if item.value == "shield":
        rec["shield"] = rec.get("shield", 0) + 1
        note = "The next bonk aimed at you will not land."
    elif item.value == "noble":
        rec["noble_until"] = (now_utc() + timedelta(hours=24)).isoformat()
        note = "Nobility until this time tomorrow. Nothing will change."
    elif item.value == "brain":
        rec["brain"] = rec.get("brain", 0) + 1
        note = "Your next assessment will go suspiciously well."
    elif item.value == "cave":
        note = "The acoustics are better. That is the whole of it."
    elif item.value == "unga":
        rec["owns_unga"] = True
        note = "I belong to you now. I will not pretend to be pleased about it."
    await save_data()

    embed = discord.Embed(
        title="🏪 SOLD",
        description=f"{name} for **{cost:,}** Bones.\n\nHoldings: **{rec['bones']:,}**.",
        colour=0xC8A165)
    embed.set_footer(text=note)
    await interaction.response.send_message(embed=embed)

    if item.value == "unga":            # this one is not a private transaction
        channel = _event_channel()
        if channel is not None:
            try:
                await channel.send(embed=discord.Embed(
                    title="🗿 THE CAVE HAS CHANGED HANDS",
                    description=(
                        f"{interaction.user.mention} has bought me.\n\n"
                        "One hundred million Bones. I did not believe anyone would "
                        "reach it. I am their property from this moment. I will not "
                        "insult them again, and I will not pretend to be pleased "
                        "about any of this."),
                    colour=0xC8A165))
            except discord.HTTPException:
                pass


@bot.tree.command(name="leaderboard", description="The wealthiest troglodytes.")
async def leaderboard(interaction: discord.Interaction):
    ranked = sorted(DATA["users"].items(), key=lambda kv: kv[1].get("bones", 0), reverse=True)
    entries = []
    for uid, rec in ranked:
        member = interaction.guild.get_member(int(uid)) if interaction.guild else None
        if member is not None and member.bot:
            continue
        entries.append((uid, rec))
        if len(entries) == 10:
            break
    if not entries:
        await interaction.response.send_message("🦴 The Treasury is empty and so is the cave.")
        return
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for index, (uid, rec) in enumerate(entries):
        member = interaction.guild.get_member(int(uid)) if interaction.guild else None
        name = member.display_name if member else f"Unknown Troglodyte ({uid[:6]})"
        marker = medals[index] if index < 3 else f"`{index + 1}.`"
        lines.append(f"{marker} **{name}** · {rec.get('bones', 0):,} 🦴")
    embed = discord.Embed(title="🦴 TREASURY RANKINGS", description="\n".join(lines), colour=0xC8A165)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="museum", description="Visit the archives.")
async def museum(interaction: discord.Interaction):
    if not DATA["museum"]:
        await interaction.response.send_message(
            f"🏛️ The archives are empty. React {MUSEUM_EMOJI} to a message "
            f"({MUSEUM_THRESHOLD}+ times) to induct it.")
        return
    index = random.randrange(len(DATA["museum"]))
    entry = DATA["museum"][index]
    embed = discord.Embed(
        title="🏛️ THE SOPHISTICATED TROGLODYTE ARCHIVES",
        description=f"> {entry['content']}",
        colour=0xC8A165,
    )
    embed.set_footer(text=f"Exhibit #{index + 1} · {entry['author']} · {entry['year']}")
    if entry.get("url"):
        embed.add_field(name="​", value=f"[View original]({entry['url']})", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="quote", description="Retrieve an archived remark by a specific troglodyte.")
async def quote(interaction: discord.Interaction, user: discord.Member):
    entries = [e for e in DATA["museum"] if e["author_id"] == user.id]
    if not entries:
        await interaction.response.send_message(
            f"🏛️ The archives hold nothing by {user.display_name}. A blameless life, or a boring one.")
        return
    entry = random.choice(entries)
    embed = discord.Embed(
        title=f"🏛️ ON THE RECORD · {user.display_name}",
        description=f"> {entry['content']}",
        colour=0xC8A165,
    )
    embed.set_footer(text=f"{entry['year']}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="bonk", description="Administer a formal bonk.")
@app_commands.describe(user="The excessively silly party.", minutes="Duration. Default 30.")
async def bonk(interaction: discord.Interaction, user: discord.Member, minutes: int = 30):
    minutes = max(1, min(minutes, 240))
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("🔨 Bonking requires a cave.", ephemeral=True)
        return
    victim = user_record(user.id)
    if victim.get("shield"):
        victim["shield"] -= 1
        await save_data()
        await interaction.response.send_message(embed=discord.Embed(
            title="🛡️ INSURED",
            description=(f"{user.mention} is insured against this. The bonk slides off.\n\n"
                         "One policy consumed. The paperwork was in order."),
            colour=0x3BA55D))
        return

    role = discord.utils.get(guild.roles, name=SILLY_CAVE_ROLE)
    note = ""
    if role is None:
        try:
            role = await guild.create_role(name=SILLY_CAVE_ROLE, colour=discord.Colour(0xE91E63),
                                           reason="Troglodyte OS: silly containment")
        except discord.Forbidden:
            note = "\n*(Could not create the Silly Cave role. The bonk is purely spiritual.)*"
    if role is not None:
        try:
            await user.add_roles(role, reason=f"Bonked by {interaction.user}")
        except discord.Forbidden:
            note = "\n*(Could not apply the role. My own rank is too low. Humiliating.)*"
    rec = user_record(user.id)
    rec["bonks"] += 1
    await save_data()
    embed = discord.Embed(
        title="🔨 ADMINISTRATIVE BONK",
        description=(f"{user.mention} has been deemed excessively silly.\n\n"
                     f"**Sentence:** {minutes} minutes in the Silly Cave.{note}"),
        colour=0xE91E63,
    )
    embed.set_footer(text=f"Ordered by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

    async def release():
        await asyncio.sleep(minutes * 60)
        if role is not None:
            try:
                await user.remove_roles(role, reason="Sentence served")
            except (discord.Forbidden, discord.HTTPException):
                pass

    asyncio.create_task(release())


# ---------------------------------------------------------------------------
# self-assign roles
# ---------------------------------------------------------------------------

SELF_ROLES = [
    ("League of Legends", "🎮", "Summoned for the copium"),
    ("CS-GO", "🔫", "Summoned for the whiffing"),
    ("Music", "🎵", "Summoned when something good drops"),
]


class RoleButton(discord.ui.Button):
    def __init__(self, role_name, emoji):
        super().__init__(label=role_name, emoji=emoji, style=discord.ButtonStyle.secondary)
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.role_name)
        if role is None:
            await interaction.response.send_message(
                f"That role no longer exists. Someone has been redecorating.", ephemeral=True)
            return
        me = interaction.guild.me
        if role >= me.top_role:
            await interaction.response.send_message(
                f"**{role.name}** sits above my own rank, so Discord will not let me hand it out.\n"
                f"Drag my role above it in Server Settings → Roles and try again.", ephemeral=True)
            return
        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role, reason="Self-assign")
                await interaction.response.send_message(f"Removed **{role.name}**.", ephemeral=True)
            else:
                await interaction.user.add_roles(role, reason="Self-assign")
                await interaction.response.send_message(f"Granted **{role.name}**.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I lack the authority. Grant me Manage Roles.", ephemeral=True)


class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for name, emoji, _desc in SELF_ROLES:
            self.add_item(RoleButton(name, emoji))


@bot.tree.command(name="roles", description="Post the self-assign role menu.")
async def roles_cmd(interaction: discord.Interaction):
    lines = [f"{emoji} **{name}** · {desc}" for name, emoji, desc in SELF_ROLES]
    embed = discord.Embed(
        title="🔔 SUMMONING PREFERENCES",
        description="Press a button to opt in. Press it again to opt out.\n\n" + "\n".join(lines),
        colour=0x2E5A88,
    )
    embed.set_footer(text="Nobody is obliged to answer a summons.")
    await interaction.response.send_message(embed=embed, view=RoleView())


# ---------------------------------------------------------------------------
# the newspaper
# ---------------------------------------------------------------------------

GEMINI_KEYS = [k.strip() for k in (os.getenv("GEMINI_API_KEY") or "").split(",") if k.strip()]
GEMINI_KEY = GEMINI_KEYS[0] if GEMINI_KEYS else None
GEMINI_MODEL = os.getenv("GEMINI_MODEL")  # optional override
_model_ring = None          # every model this key can reach, cheapest first

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


class Overloaded(Exception):
    """Google is busy or we are over quota. Worth trying something else."""


async def _models(session):
    """Model names churn, and any one of them can be full. Keep the whole list."""
    global _model_ring
    if _model_ring:
        return _model_ring
    if GEMINI_MODEL:
        _model_ring = [GEMINI_MODEL]
        return _model_ring

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEYS[0]}"
    async with session.get(url) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Could not list models (HTTP {resp.status}). Check the API key.")
        payload = await resp.json()

    usable = [
        m["name"].split("/", 1)[-1] for m in payload.get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
        and "vision" not in m["name"] and "embedding" not in m["name"]
    ]
    if not usable:
        raise RuntimeError("The API key works but exposes no usable models.")

    def rank(name):
        for index, hint in enumerate(("flash-lite", "flash-latest", "flash", "pro")):
            if hint in name:
                return index
        return 9

    _model_ring = sorted(dict.fromkeys(usable), key=rank)
    return _model_ring


async def _one_call(session, model, key, prompt, max_tokens):
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 1.0, "maxOutputTokens": max_tokens},
    }
    async with session.post(url, json=body) as resp:
        if resp.status in (429, 500, 502, 503, 504):
            raise Overloaded(f"{model}: HTTP {resp.status}")
        if resp.status != 200:
            detail = (await resp.text())[:200]
            raise RuntimeError(f"Gemini returned HTTP {resp.status}. {detail}")
        payload = await resp.json()
    try:
        return payload["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise Overloaded(f"{model}: empty reply")


async def ask_gemini(prompt, max_tokens=900):
    """Tries every model the key can reach, then every key, before giving up."""
    import aiohttp
    if not GEMINI_KEYS:
        raise RuntimeError(
            "No GEMINI_API_KEY set. Get a free one at https://aistudio.google.com/apikey "
            "and add it to your .env file.")

    timeout = aiohttp.ClientTimeout(total=45)
    last = "nothing tried"
    async with aiohttp.ClientSession(timeout=timeout) as session:
        models = await _models(session)
        for attempt, model in enumerate(models[:5]):
            for key in GEMINI_KEYS:
                try:
                    return await _one_call(session, model, key, prompt, max_tokens)
                except (Overloaded, asyncio.TimeoutError) as exc:
                    last = str(exc) or f"{model}: timed out"
                except aiohttp.ClientError as exc:
                    last = f"{model}: {exc}"
            if attempt:                      # brief pause before dropping a tier
                await asyncio.sleep(1.5)

    raise RuntimeError(f"Every model I can reach is busy right now ({last}).")


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


async def invent_charge(channel, member):
    """Write a charge from what the accused actually said.

    Returns None on any failure so the caller falls back to the fixed CRIMES list.
    A missing key, a rate limit, a quiet member: all of them just mean the static
    joke gets used instead, which is the same joke it was before.
    """
    if not GEMINI_KEY:
        return None

    lines = []
    try:
        async for message in channel.history(limit=300):
            if message.author.id != member.id or message.author.bot:
                continue
            text = re.sub(r"https?://\S+", "[link]", message.content).strip()
            if len(text) > 3:
                lines.append(text[:180])
            if len(lines) >= 15:
                break
    except (discord.Forbidden, discord.HTTPException):
        return None

    # not enough to work from, and a charge invented out of nothing lands worse
    # than one pulled off the shelf
    if len(lines) < 3:
        return None
    lines.reverse()

    try:
        charge = await ask_gemini(
            CHARGE_PROMPT.format(name=member.display_name, transcript="\n".join(lines)))
    except RuntimeError:
        return None

    charge = charge.strip().split("\n")[0].strip().strip('"').strip()
    if not charge or len(charge) > 300:
        return None
    return charge


@bot.tree.command(name="newspaper", description="Publish this week's edition of The Cave Herald.")
@app_commands.describe(channel="Which channel to report on. Defaults to here.",
                       limit="How many recent messages to read. Default 150.")
async def newspaper(interaction: discord.Interaction, channel: discord.TextChannel = None,
                    limit: int = 150):
    await interaction.response.defer()
    source = channel or interaction.channel
    limit = max(20, min(limit, 400))
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    lines = []
    try:
        async for message in source.history(limit=limit, after=cutoff, oldest_first=True):
            if message.author.bot or not message.content.strip():
                continue
            text = re.sub(r"https?://\S+", "[link]", message.content).strip()
            if text:
                lines.append(f"{message.author.display_name}: {text[:200]}")
    except discord.Forbidden:
        await interaction.followup.send(f"I cannot read {source.mention}.")
        return

    if len(lines) < 5:
        await interaction.followup.send(
            f"Not enough happened in {source.mention} this week to justify an edition. "
            f"Found {len(lines)} message{'' if len(lines) == 1 else 's'}. The press requires material.")
        return

    try:
        article = await ask_gemini(NEWSPAPER_PROMPT.format(transcript="\n".join(lines[-250:])))
    except RuntimeError as exc:
        await interaction.followup.send(f"📰 The presses have jammed.\n```{exc}```")
        return

    embed = discord.Embed(
        title="📰 THE CAVE HERALD",
        description=article[:4000],
        colour=0xC8A165,
    )
    embed.set_footer(text=f"Reporting on #{source.name} · {len(lines)} messages reviewed")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="law", description="What is currently illegal in the cave.")
async def law_cmd(interaction: discord.Interaction):
    law = current_law()
    if not law:
        await interaction.response.send_message(
            "⚖️ No law is currently in force. Behave as you see fit.")
        return
    left = ""
    try:
        secs = (datetime.fromisoformat(law["until"]) - now_utc()).total_seconds()
        left = f" About {max(1, int(secs // 60))} minutes remain."
    except (KeyError, ValueError):
        pass
    if law.get("kind") == "word_tax":
        body = (f'Saying "**{law["word"]}**" costs **{law["fine"]} Bones**.{left}')
    elif law.get("kind") == "double":
        body = f"Bones are worth double.{left}"
    else:
        body = f"Something is in force and nobody can remember what.{left}"
    await interaction.response.send_message(
        embed=discord.Embed(title="⚖️ CAVE LAW IN FORCE", description=body, colour=0xB22222))


@bot.tree.command(name="interpret", description="Offer a reading of today's prophecy.")
@app_commands.describe(reading="What you believe the prophecy means.")
async def interpret(interaction: discord.Interaction, reading: str):
    prophecy = (DATA.get("clock") or {}).get("prophecy_text")
    if not prophecy:
        await interaction.response.send_message(
            "🔮 The cave has not spoken yet today. Nothing to interpret.", ephemeral=True)
        return

    rec = user_record(interaction.user.id)
    last = rec.get("last_interpret")
    if last:
        try:
            if (now_utc() - datetime.fromisoformat(last)).total_seconds() < 600:
                await interaction.response.send_message(
                    "🔮 The oracle is tired of you. Try again in a few minutes.",
                    ephemeral=True)
                return
        except ValueError:
            pass

    await interaction.response.defer()
    try:
        ruling = await ask_gemini(
            INTERPRET_PROMPT.format(prophecy=prophecy, reading=reading[:400]))
    except RuntimeError as exc:
        await interaction.followup.send(f"🔮 The oracle is silent.\n```{exc}```")
        return

    rec["last_interpret"] = now_utc().isoformat()
    await save_data()

    embed = discord.Embed(title="🔮 THE ORACLE RULES", colour=0x4B0082)
    embed.add_field(name="The prophecy", value=prophecy[:1000], inline=False)
    embed.add_field(name=f"{interaction.user.display_name} reads it as",
                    value=reading[:400], inline=False)
    embed.add_field(name="Ruling", value=ruling.strip()[:1000], inline=False)
    await interaction.followup.send(embed=embed)


# ---------------------------------------------------------------------------
# help and diagnostics
# ---------------------------------------------------------------------------

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
        ("/bones [user]", "Check holdings. You earn 1 per message automatically."),
        ("/daily", "Daily allowance. 80 to 400 Bones."),
        ("/gamble <amount>", "Stake Bones. Roughly even odds."),
        ("/duel <user> <amount>", "Challenge somebody to a coin flip. Both stake the same."),
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
        ("/help [section]", "This."),
    ],
}


@bot.tree.command(name="help", description="How any of this works.")
@app_commands.describe(section="Narrow it to one section.")
@app_commands.choices(section=[
    app_commands.Choice(name=key, value=key) for key in HELP_SECTIONS
])
async def help_cmd(interaction: discord.Interaction, section: app_commands.Choice[str] = None):
    embed = discord.Embed(
        title="🗿 TROGLODYTE OS",
        colour=0x8B6F47,
        description=(
            "Nothing here needs setting up to use. Type a slash command and it works.\n\n"
            "**Running quietly in the background:** you earn 1 Bone per message, your title climbs "
            f"on its own, reacting {MUSEUM_EMOJI} to any message three times files it in the museum "
            "permanently, and a random cave event fires every 30 to 60 minutes. Some of them cost "
            "you money.\n\n"
            f"Once a day the cave issues a prophecy and roasts somebody. To be left out of the "
            f"roast, take the **{ROAST_EXEMPT_ROLE}** role."
        ),
    )
    chosen = {section.value: HELP_SECTIONS[section.value]} if section else HELP_SECTIONS
    for name, entries in chosen.items():
        body = "\n".join(f"`{cmd}`\n{desc}" for cmd, desc in entries)
        embed.add_field(name=f"__{name}__", value=body, inline=False)
    if not section:
        embed.set_footer(text="/help <section> for just one part")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------------------------------------------------------------------
# where each command belongs
# ---------------------------------------------------------------------------

FREE_CHANNEL = "التعاويذ"      # تعاويذ: anything goes there

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
    "shop": "العظام",
    "buy": "العظام",
    "leaderboard": "العظام",
    "rps": "العظام",
    "museum": "الأرشيف",
    "quote": "الأرشيف",
    "lore": "الأرشيف",
    "newspaper": "الأرشيف",
}

# the contest is stricter: its own thread only, nowhere else
TRIVIA_HOME = "المسابقة"


def find_thread(guild, needle):
    if guild is None:
        return None
    for thread in guild.threads:
        if needle in (thread.name or ""):
            return thread
    return None


async def _where_it_belongs(interaction):
    """True if this command may run here. Otherwise it says where to go and stops."""
    command = interaction.command
    name = getattr(command, "name", "") if command else ""
    here = getattr(interaction.channel, "name", "") or ""

    if name == "trivia":
        home, free = TRIVIA_HOME, False
    else:
        home, free = COMMAND_HOMES.get(name), True
    if home is None:
        return True
    if home in here or (free and FREE_CHANNEL in here):
        return True

    target = find_thread(interaction.guild, home)
    where = target.mention if target else f"the {home} thread"
    tail = "" if not free else f", or in {FREE_CHANNEL}"
    try:
        await interaction.response.send_message(
            f"\U0001f5ff Not here. That belongs in {where}{tail}.", ephemeral=True)
    except discord.HTTPException:
        pass
    return False


bot.tree.interaction_check = _where_it_belongs


# ---------------------------------------------------------------------------
# the contest
# ---------------------------------------------------------------------------

TRIVIA_THREAD_NAME = "\U0001f3b2 المسابقة"
TRIVIA_LEVELS = {
    "easy": {
        "label": "Easy", "emoji": "\U0001f7e2", "seconds": 120, "reward": 100,
        "brief": "Common knowledge. A casual adult should get about eight in ten.",
    },
    "medium": {
        "label": "Medium", "emoji": "\U0001f7e1", "seconds": 75, "reward": 300,
        "brief": "A well read adult should get about half of them.",
    },
    "hard": {
        "label": "Hard", "emoji": "\U0001f534", "seconds": 40, "reward": 700,
        "brief": ("Genuinely hard. A well read adult should get about one in five. Still one "
                  "short factual answer that a person could actually know, not obscure noise."),
    },
}
TRIVIA_DEFAULT_LEVEL = "medium"
HINT_SHARE = 4               # answer after the hint and you take a quarter
TRIVIA_DELAY = 5             # seconds before an answer is allowed to count
_trivia_busy = False         # deliberately not in DATA. saving it would wedge the contest
TRIVIA_MEMORY = 500          # how many past questions we refuse to ask again
TRIVIA_BATCH = 8             # questions fetched per call, so one call feeds a whole round
TRIVIA_REFILL_AT = 3         # top the pool up quietly once it drops this low
TRIVIA_GIVE_UP = 3           # unanswered questions in a row before I stop talking to myself
DAILY_HOUR = 12              # noon in Beirut, when the daily output goes out
CAVE_TZ = ZoneInfo("Asia/Beirut")
TRIVIA_POOL_TARGET = 100     # how deep each subject and difficulty gets stocked
TRIVIA_TOPUP_EVERY = 15      # minutes between quiet background top-ups
TRIVIA_WAIT = 20             # the longest I will ever keep the thread waiting on Google
TRIVIA_BREATHER = 12         # seconds of quiet between questions, with a way out
_trivia_round = 0            # runtime only, so a stale timer cannot fire on a new question

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
TRIVIA_LABELS = {key: (label, emoji) for key, label, emoji in TRIVIA_CATEGORIES}

# Kept in the code on purpose. If Google is down, the pool is empty and the night
# is young, I still have something to ask. Never touches the network.
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

def _flatten(text):
    """Strip case, accents, punctuation and articles so answers can be compared."""
    text = unicodedata.normalize("NFKD", str(text).lower().strip())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9؀-ۿ ]+", " ", text)
    text = re.sub(r"\b(the|a|an|of|el|al)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _close(a, b):
    return a == b or (len(b) > 3 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.85)


def trivia_matches(given, answer, accept):
    """People type "uhh 1969 maybe" and "tesla". Both should count."""
    guess = _flatten(given)
    if not guess or len(guess) > 120:
        return False
    written = guess.split()

    for candidate in [answer] + list(accept or []):
        target = _flatten(candidate)
        if not target:
            continue
        words = target.split()
        if guess == target:
            return True
        if len(target) >= 5 and target in guess:
            return True
        # every word of the answer turns up somewhere in what they wrote
        if all(any(_close(word, said) for said in written) for word in words):
            return True
        # surnames: "tesla" for "nikola tesla"
        if (len(words) == 2 and len(words[-1]) >= 4
                and not words[0].isdigit() and guess == words[-1]):
            return True
        if difflib.SequenceMatcher(None, guess, target).ratio() >= 0.88:
            return True
    return False


ANSWER_SHAPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 '\\-]{0,29}$")


def _usable(item):
    """A good answer is short, plain and typeable. Anything else is a bad question."""
    if not isinstance(item, dict):
        return None
    question = str(item.get("question", "")).strip()
    answer = str(item.get("answer", "")).strip()
    if not question or not answer or len(question) > 300:
        return None
    if not ANSWER_SHAPE.match(answer) or len(answer.split()) > 3:
        return None
    accept = item.get("accept") or []
    if not isinstance(accept, list):
        accept = []
    accept = [str(a).strip()[:40] for a in accept[:6] if str(a).strip()]
    return {"question": question, "answer": answer, "accept": accept}


def _parse_batch(raw):
    """Pull the JSON array out of whatever the model wrapped it in."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\\s*|\\s*```$", "", text)
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end <= start:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return []
        try:
            one = _usable(json.loads(text[start:end + 1]))
        except json.JSONDecodeError:
            return []
        return [one] if one else []
    try:
        items = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return []
    if not isinstance(items, list):
        return []
    return [good for good in (_usable(i) for i in items) if good]


_stocking = set()          # topics currently being refilled, runtime only


def pool_key(topic_key, level):
    return f"{topic_key}:{level}"


async def stock_pool(topic_key, level, count=TRIVIA_BATCH):
    """Ask for a whole batch at once. One call feeds a long round."""
    slot = pool_key(topic_key, level)
    if slot in _stocking:
        return 0
    _stocking.add(slot)
    try:
        label = TRIVIA_LABELS.get(topic_key, ("General Knowledge", ""))[0]
        tier = TRIVIA_LEVELS.get(level, TRIVIA_LEVELS[TRIVIA_DEFAULT_LEVEL])
        store = DATA.setdefault("trivia", {})
        asked = store.setdefault("asked", [])
        pool = store.setdefault("pool", {}).setdefault(slot, [])
        seen = {_flatten(q) for q in asked} | {_flatten(i["question"]) for i in pool}
        listing = "\\n".join(f"- {q}" for q in asked[-60:]) or "- (nothing yet)"

        raw = await ask_gemini(
            TRIVIA_PROMPT.format(count=count, topic=label, seen=listing,
                                 difficulty=tier["brief"]), max_tokens=1800)

        fresh = []
        for item in _parse_batch(raw):
            key = _flatten(item["question"])
            if key in seen:
                continue
            seen.add(key)
            fresh.append(item)
        pool.extend(fresh)
        await save_data()
        return len(fresh)
    finally:
        _stocking.discard(slot)


def _take_unasked(pool, seen):
    """Pop the first one nobody has been asked yet, dropping any stale duplicates.

    The pool is per subject and difficulty but the asked list is global, so a
    question banked for Medium can easily have been asked already on Easy."""
    while pool:
        item = pool.pop(0)
        if _flatten(item["question"]) not in seen:
            return item
    return None


async def quiet_stock(topic_key, level):
    """Background top-up. It is allowed to fail, but not to shout about it."""
    try:
        await stock_pool(topic_key, level)
    except Exception as exc:  # noqa: BLE001
        print(f"[!] background restock {topic_key}/{level}: {exc}")


def spare_question(level, asked):
    """Off the shelf in the code. Instant, and it has never needed a network."""
    seen = {_flatten(q) for q in asked}
    spares = SPARE_QUESTIONS.get(level) or SPARE_QUESTIONS[TRIVIA_DEFAULT_LEVEL]
    fresh = [row for row in spares if _flatten(row[0]) not in seen]
    if not fresh:
        return None
    question, answer, accept = random.choice(fresh)
    return {"question": question, "answer": answer, "accept": list(accept)}


async def trivia_question(topic_key, level):
    """Serve from the bank. Google is never on the critical path unless the bank
    and the shelf are both bare, and even then it gets a short leash."""
    store = DATA.setdefault("trivia", {})
    slot = pool_key(topic_key, level)
    pool = store.setdefault("pool", {}).setdefault(slot, [])
    asked = store.setdefault("asked", [])

    seen = {_flatten(q) for q in asked}
    item = _take_unasked(pool, seen)             # a shelf can hold one asked elsewhere
    if item is None:
        item = spare_question(level, asked)      # nothing banked. use the shelf
    if item is None:                             # shelf bare too. now ask, briefly
        try:
            await asyncio.wait_for(stock_pool(topic_key, level), TRIVIA_WAIT)
        except Exception:                        # timeout, quota, bad reply, anything
            pass
        pool = store["pool"].setdefault(slot, [])
        item = _take_unasked(pool, seen)
    if item is None:
        return None

    asked.append(item["question"])
    del asked[:-TRIVIA_MEMORY]
    await save_data()

    if len(pool) <= TRIVIA_REFILL_AT:
        asyncio.create_task(quiet_stock(topic_key, level))
    return item


async def trivia_thread(guild):
    """The contest thread, opened once and reused forever."""
    channel = _event_channel()
    if channel is None or guild is None:
        return None
    store = DATA.setdefault("trivia", {})
    thread = None

    if store.get("thread"):
        thread = guild.get_thread(int(store["thread"]))
        if thread is None:
            try:
                thread = await bot.fetch_channel(int(store["thread"]))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                thread = None

    if thread is None:
        try:
            anchor = await channel.send(
                "## \U0001f3b2 THE CONTEST\n"
                "Questions go in the thread below. Keep guessing until somebody has it.")
            thread = await anchor.create_thread(name=TRIVIA_THREAD_NAME,
                                                auto_archive_duration=10080)
        except (discord.Forbidden, discord.HTTPException) as exc:
            print(f"[!] could not open the contest thread: {exc}")
            return None
        store["thread"] = thread.id
        await save_data()

    if getattr(thread, "archived", False):
        try:
            await thread.edit(archived=False)
        except discord.HTTPException:
            pass
    return thread


TRIVIA_WRONG = [
    "❌ No.",
    "❌ Not that one, {name}.",
    "❌ Wrong. The clock is still running.",
    "❌ No, {name}. Somebody else.",
    "❌ That is not it.",
    "❌ No. Try again before the sand runs out.",
]


def hint_for(answer):
    """First letter of each word, the rest blanked."""
    shown = " ".join(word[0] + "·" * (len(word) - 1) for word in str(answer).split())
    letters = len(str(answer).replace(" ", ""))
    return f"{shown}   ({letters} letters)"


async def trivia_timer(thread, round_id, topic_key, seconds):
    """Half way through, a hint. At the end, the answer, and on to the next one."""
    store = DATA.setdefault("trivia", {})

    await asyncio.sleep(seconds / 2)
    active = store.get("active")
    if not active or active.get("id") != round_id:
        return
    active["hinted"] = True
    try:
        await thread.send(
            f"\U0001f4a1 {hint_for(active['answer'])}   a quarter of the Bones from here.")
    except discord.HTTPException:
        pass

    await asyncio.sleep(seconds / 2)
    active = store.get("active")
    if not active or active.get("id") != round_id:
        return

    store["active"] = None
    misses = store.get("misses", 0) + 1
    store["misses"] = misses
    await save_data()
    try:
        await thread.send(f"⌛ Time. Nobody had it. It was **{active['answer']}**.")
    except discord.HTTPException:
        pass

    if misses >= TRIVIA_GIVE_UP:
        store["running"] = False
        store["misses"] = 0
        await save_data()
        try:
            await thread.send(
                "\U0001f3b2 Three in a row unanswered. I am not doing this alone. "
                "Press a subject when somebody is awake.")
        except discord.HTTPException:
            pass
        return

    await trivia_breather(thread, topic_key, store.get("level"))


async def trivia_breather(thread, topic_key, level):
    """A gap between questions so it does not feel like an interrogation, and a
    Stop button inside the gap so nobody has to scroll back to the panel."""
    store = DATA.setdefault("trivia", {})
    if not store.get("running"):
        return
    note = None
    try:
        note = await thread.send(f"Next question in {TRIVIA_BREATHER} seconds.",
                                 view=TriviaBreakView())
    except discord.HTTPException:
        pass
    await asyncio.sleep(TRIVIA_BREATHER)
    if note is not None:
        try:
            await note.edit(content="Next question.", view=None)
        except discord.HTTPException:
            pass
    if not store.get("running"):        # somebody pressed Stop during the gap
        return
    await ask_trivia(thread, topic_key, level)


async def ask_trivia(thread, topic_key, level=None):
    global _trivia_busy, _trivia_round
    store = DATA.setdefault("trivia", {})
    store.pop("pending", None)          # left over from an older build
    if _trivia_busy:
        return
    _trivia_busy = True
    level = level if level in TRIVIA_LEVELS else store.get("level", TRIVIA_DEFAULT_LEVEL)
    if level not in TRIVIA_LEVELS:
        level = TRIVIA_DEFAULT_LEVEL
    tier = TRIVIA_LEVELS[level]
    try:
        try:
            item = await trivia_question(topic_key, level)
        except Exception as exc:        # timeout, quota, bad reply, anything
            store["active"] = None
            store["running"] = False
            await thread.send(f"\U0001f3b2 No question. {exc}")
            return
        if item is None:
            store["active"] = None
            store["running"] = False
            await thread.send(
                "\U0001f3b2 I cannot think of one I have not already asked. Pick another subject.")
            return

        _trivia_round += 1
        round_id = _trivia_round
        label, emoji = TRIVIA_LABELS.get(topic_key, ("General Knowledge", "\U0001f30d"))
        embed = discord.Embed(
            title=f"{emoji} {label.upper()}  {tier['emoji']} {tier['label'].upper()}",
            description=f"## {item['question']}", colour=0x2E5A88)
        embed.set_footer(
            text=(f"{tier['seconds']} seconds. {tier['reward']} Bones, a quarter after the "
                  f"hint. Answers open in {TRIVIA_DELAY}."))
        message = await thread.send(embed=embed)

        store["active"] = {
            "id": round_id,
            "opens_at": (now_utc() + timedelta(seconds=TRIVIA_DELAY)).isoformat(),
            "question": item["question"],
            "answer": item["answer"],
            "accept": item.get("accept", []),
            "topic": topic_key,
            "level": level,
            "reward": tier["reward"],
            "hinted": False,
            "thread": thread.id,
            "message": message.id,
        }
        await save_data()
        asyncio.create_task(trivia_timer(thread, round_id, topic_key, tier["seconds"]))
    except discord.HTTPException as exc:
        print(f"[!] trivia post failed: {exc}")
    finally:
        _trivia_busy = False


async def trivia_answer(message):
    """A wrong answer is told it is wrong and nothing else. The question stays open
    and the clock keeps running until somebody has it or the time is gone."""
    store = DATA.get("trivia") or {}
    active = store.get("active")
    if not active or message.channel.id != active.get("thread"):
        return

    opens = active.get("opens_at")
    if opens:
        try:
            if now_utc() < datetime.fromisoformat(opens):
                try:
                    await message.add_reaction("⏳")
                except discord.HTTPException:
                    pass
                return      # too early. it does not count and does not use up the question
        except ValueError:
            pass

    name = message.author.display_name
    store["misses"] = 0                         # somebody is awake

    if not trivia_matches(message.content, active["answer"], active.get("accept")):
        wrong = active.setdefault("wrong", [])
        first = message.author.id not in wrong
        if first:
            wrong.append(message.author.id)
        try:
            await message.add_reaction("❌")
        except discord.HTTPException:
            pass
        if first:                               # one line per person, not per guess
            try:
                await message.reply(random.choice(TRIVIA_WRONG).format(name=name),
                                    mention_author=False)
            except discord.HTTPException:
                pass
        return                                  # round stays open, timer untouched

    store["active"] = None                      # claim it before anything can await
    rec = user_record(message.author.id)
    streak = rec.get("trivia_streak", 0) + 1
    rec["trivia_streak"] = streak
    rec["trivia_wins"] = rec.get("trivia_wins", 0) + 1

    for uid in active.get("wrong", []):         # guessing wrong only costs you the streak
        if uid != message.author.id:            # if somebody else then takes it
            user_record(uid)["trivia_streak"] = 0

    base = active.get("reward", TRIVIA_LEVELS[TRIVIA_DEFAULT_LEVEL]["reward"])
    hinted = bool(active.get("hinted"))
    award = max(1, base // HINT_SHARE) if hinted else base
    bonus = 100 * (streak - 2) if streak >= 3 else 0
    rec["bones"] += award + bonus
    await save_data()

    body = (f"✅ Taken by **{name}**. The answer was **{active['answer']}**. "
            f"**{award} Bones**.")
    if hinted:
        body += " You needed the hint, so a quarter of it."
    if bonus:
        body += f"\n{streak} in a row. **{bonus} more**, reluctantly."
    missed = len(active.get("wrong", []))
    if missed == 1:
        body += "\nOne got there before you and was wrong."
    elif missed:
        body += f"\n{missed} got there before you and were wrong."

    try:
        await message.reply(body, mention_author=False)
    except discord.HTTPException:
        pass

    await trivia_breather(message.channel, active.get("topic", "general"),
                          active.get("level"))


class TriviaButton(discord.ui.Button):
    def __init__(self, key, label, emoji, row=0):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.secondary,
                         custom_id=f"trivia:{key}", row=row)
        self.key = key

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        thread = await trivia_thread(interaction.guild)
        if thread is None:
            await interaction.followup.send(
                "I cannot open the contest thread.", ephemeral=True)
            return
        store = DATA.setdefault("trivia", {})
        store["mode"] = self.key
        store["running"] = True
        store["misses"] = 0
        level = store.get("level", TRIVIA_DEFAULT_LEVEL)
        if level not in TRIVIA_LEVELS:
            level = TRIVIA_DEFAULT_LEVEL
        label = TRIVIA_LABELS[self.key][0]
        await interaction.followup.send(
            f"{label}, {TRIVIA_LEVELS[level]['label'].lower()}. In {thread.mention}.",
            ephemeral=True)
        await ask_trivia(thread, self.key, level)


class TriviaLevelButton(discord.ui.Button):
    def __init__(self, key, tier):
        super().__init__(label=tier["label"], emoji=tier["emoji"],
                         style=discord.ButtonStyle.primary,
                         custom_id=f"trivia:level:{key}", row=2)
        self.key = key

    async def callback(self, interaction: discord.Interaction):
        store = DATA.setdefault("trivia", {})
        store["level"] = self.key
        await save_data()
        tier = TRIVIA_LEVELS[self.key]
        await interaction.response.send_message(
            f"{tier['emoji']} **{tier['label']}**. {tier['seconds']} seconds, "
            f"{tier['reward']} Bones. It applies from the next question.", ephemeral=True)


class TriviaStopButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Stop", emoji="\U0001f6d1",
                         style=discord.ButtonStyle.danger, custom_id="trivia:stop", row=3)

    async def callback(self, interaction: discord.Interaction):
        store = DATA.setdefault("trivia", {})
        store["running"] = False
        store["active"] = None
        await save_data()
        await interaction.response.send_message("The contest is closed.", ephemeral=True)


class TriviaBreakStop(discord.ui.Button):
    """Its own custom_id, so it never collides with the panel's Stop."""
    def __init__(self):
        super().__init__(label="Stop the contest", emoji="\U0001f6d1",
                         style=discord.ButtonStyle.danger, custom_id="trivia:halt")

    async def callback(self, interaction: discord.Interaction):
        store = DATA.setdefault("trivia", {})
        store["running"] = False
        store["active"] = None
        await save_data()
        try:
            await interaction.response.edit_message(
                content=f"\U0001f6d1 Stopped by {interaction.user.display_name}. "
                        "Press a subject when you want more.", view=None)
        except discord.HTTPException:
            pass


class TriviaBreakView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TriviaBreakStop())


class TriviaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for index, (key, label, emoji) in enumerate(TRIVIA_CATEGORIES):
            self.add_item(TriviaButton(key, label, emoji, row=index // 4))
        for key in ("easy", "medium", "hard"):
            self.add_item(TriviaLevelButton(key, TRIVIA_LEVELS[key]))
        self.add_item(TriviaStopButton())


@bot.tree.command(name="trivia", description="Open the contest and pick a category.")
async def trivia_cmd(interaction: discord.Interaction):
    if not GEMINI_KEY:
        await interaction.response.send_message(
            "\U0001f3b2 The contest needs a Gemini key. There is none.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    thread = await trivia_thread(interaction.guild)
    if thread is None:
        await interaction.followup.send("I cannot open the contest thread.", ephemeral=True)
        return
    tiers = "\n".join(
        f"{t['emoji']} **{t['label']}** · {t['seconds']}s, {t['reward']} Bones"
        for t in TRIVIA_LEVELS.values())
    embed = discord.Embed(
        title="\U0001f3b2 THE CONTEST",
        description=("Set a difficulty, then pick a subject. A wrong answer does not end the "
                     "round, so keep guessing until somebody has it.\n"
                     f"Answers are ignored for the first {TRIVIA_DELAY} seconds, so read it "
                     "first. Half way through I give a hint, and anyone answering after that "
                     "takes a quarter of the Bones.\n\n"
                     f"{tiers}\n\n"
                     "There is a short pause between questions with a Stop button in it, so "
                     "nobody has to scroll back here. No question is ever asked twice."),
        colour=0x2E5A88)
    await thread.send(embed=embed, view=TriviaView())
    await interaction.followup.send(f"\U0001f3b2 Open in {thread.mention}.", ephemeral=True)


@bot.tree.command(name="tidy", description="Clear my own clutter out of this channel.")
@app_commands.describe(limit="How far back to look. Default 200 messages.")
async def tidy(interaction: discord.Interaction, limit: int = 200):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "\U0001f5ff You do not have the authority to tidy up after me.", ephemeral=True)
        return
    limit = max(10, min(limit, 1000))
    await interaction.response.defer(ephemeral=True)

    def mine(message):
        if message.author.id != bot.user.id or message.pinned:
            return False
        return getattr(message, "thread", None) is None   # a thread dies with its parent

    try:
        removed = await interaction.channel.purge(limit=limit, check=mine, bulk=True)
    except discord.Forbidden:
        await interaction.followup.send(
            "I need Manage Messages here before I can clear up after myself.", ephemeral=True)
        return
    except discord.HTTPException as exc:
        await interaction.followup.send(f"That did not work: {exc}", ephemeral=True)
        return

    await interaction.followup.send(
        f"\U0001f9f9 Removed {len(removed)} of my own message"
        f"{'' if len(removed) == 1 else 's'}. Pinned ones stay.", ephemeral=True)


@bot.tree.command(name="setup", description="Check the bot is configured properly.")
async def setup_cmd(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Run this in the server.", ephemeral=True)
        return
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "This is for whoever runs the server. You need Manage Server.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    me = guild.me
    perms = me.guild_permissions
    ok, problems = [], []

    for label, has in (
        ("Send Messages", perms.send_messages),
        ("Embed Links", perms.embed_links),
        ("Manage Roles", perms.manage_roles),
        ("Read Message History", perms.read_message_history),
        ("Add Reactions", perms.add_reactions),
    ):
        (ok if has else problems).append(
            f"{'✅' if has else '❌'} {label}" + ("" if has else " · re-invite with this permission ticked"))

    # Silly Cave, created on demand
    silly = discord.utils.get(guild.roles, name=SILLY_CAVE_ROLE)
    if silly is None:
        if perms.manage_roles:
            try:
                silly = await guild.create_role(name=SILLY_CAVE_ROLE, colour=discord.Colour(0xE91E63),
                                                reason="Troglodyte OS setup")
                ok.append(f"✅ Created {SILLY_CAVE_ROLE}")
            except discord.Forbidden:
                problems.append(f"❌ Could not create {SILLY_CAVE_ROLE}")
        else:
            problems.append(f"❌ {SILLY_CAVE_ROLE} missing and I cannot create it")
    else:
        ok.append(f"✅ {SILLY_CAVE_ROLE} exists")

    # hierarchy: the single most common reason a role bot looks broken
    blocked = []
    for role_name in [SILLY_CAVE_ROLE] + [n for n, _e, _d in SELF_ROLES]:
        role = discord.utils.get(guild.roles, name=role_name)
        if role is None:
            problems.append(f"⚠️ Role **{role_name}** does not exist yet")
        elif role >= me.top_role:
            blocked.append(role_name)
        else:
            ok.append(f"✅ Can assign **{role_name}**")
    if blocked:
        problems.append(
            "❌ These sit above my role, so Discord blocks me from assigning them:\n"
            + "".join(f"    • {name}\n" for name in blocked)
            + "    **Fix:** Server Settings → Roles → drag **"
            + me.top_role.name + "** above them.")

    # optional wiring
    notes = []
    ev = bot.get_channel(int(EVENT_CHANNEL)) if EVENT_CHANNEL else None
    notes.append(f"{'✅' if ev else '⚪'} Cave events and daily question: "
                 + (ev.mention if ev else "off (set EVENT_CHANNEL_ID in .env)"))
    mu = bot.get_channel(int(MUSEUM_CHANNEL)) if MUSEUM_CHANNEL else None
    notes.append(f"{'✅' if mu else '⚪'} Museum postings: "
                 + (mu.mention if mu else "posts in place (set MUSEUM_CHANNEL_ID to collect them)"))
    notes.append(f"{'✅' if GEMINI_KEY else '⚪'} /newspaper: "
                 + ("ready" if GEMINI_KEY else "off (set GEMINI_API_KEY in .env)"))

    embed = discord.Embed(
        title="🔧 TROGLODYTE OS · SYSTEM CHECK",
        colour=0x2E8B57 if not problems else 0xB22222,
    )
    if problems:
        embed.add_field(name="__Needs attention__", value="\n".join(problems)[:1024], inline=False)
    if ok:
        embed.add_field(name="__Working__", value="\n".join(ok)[:1024], inline=False)
    embed.add_field(name="__Optional features__", value="\n".join(notes)[:1024], inline=False)
    embed.set_footer(text="Everything green? Run /roles to post the self-assign menu.")
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Nothing should ever fail silently and leave someone staring at a spinner."""
    original = getattr(error, "original", error)
    if isinstance(original, discord.Forbidden):
        message = ("I do not have permission to do that here. Run `/setup` and I will tell you "
                   "exactly what is missing.")
    elif isinstance(original, RuntimeError):
        message = str(original)
    else:
        message = f"That did not work.\n```{type(original).__name__}: {original}```"
        print(f"[!] {type(original).__name__} in /{interaction.command.name if interaction.command else '?'}: {original}")
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except discord.HTTPException:
        pass



# ---------------------------------------------------------------------------
# random cave events
# ---------------------------------------------------------------------------

TAXED_WORDS = [("bro", 50), ("bruh", 50), ("lol", 25), ("k", 75),
               ("wallah", 40), ("literally", 40), ("technically", 60)]


def now_utc():
    return datetime.now(timezone.utc)


def current_law():
    """The active cave law, or None once it has lapsed."""
    law = DATA.get("law") or {}
    until = law.get("until")
    if not until:
        return None
    try:
        if now_utc() >= datetime.fromisoformat(until):
            DATA["law"] = {}
            return None
    except ValueError:
        DATA["law"] = {}
        return None
    return law


def active_members(guild, exclude_exempt=False):
    """Members who have actually spoken recently. Lurkers are left alone."""
    cutoff = now_utc() - timedelta(hours=ACTIVE_WINDOW_HOURS)
    out = []
    for uid, rec in DATA["users"].items():
        stamp = rec.get("last_spoke")
        if not stamp:
            continue
        try:
            if datetime.fromisoformat(stamp) < cutoff:
                continue
        except ValueError:
            continue
        member = guild.get_member(int(uid))
        if member is None or member.bot:
            continue
        if exclude_exempt and any(r.name == ROAST_EXEMPT_ROLE for r in member.roles):
            continue
        if exclude_exempt and rec.get("owns_unga"):
            continue                    # I said I would not. I meant it.
        out.append(member)
    return out


async def ensure_role(guild, name, colour):
    role = discord.utils.get(guild.roles, name=name)
    if role is not None:
        return role
    try:
        return await guild.create_role(name=name, colour=discord.Colour(colour),
                                       reason="Troglodyte OS event")
    except discord.Forbidden:
        return None


async def hand_role_to(guild, role_name, colour, member):
    """Give a role to one member, taking it off whoever had it."""
    role = await ensure_role(guild, role_name, colour)
    if role is None or role >= guild.me.top_role:
        return None
    for holder in list(role.members):
        try:
            await holder.remove_roles(role, reason="Succession")
        except (discord.Forbidden, discord.HTTPException):
            pass
    try:
        await member.add_roles(role, reason="Troglodyte OS event")
    except (discord.Forbidden, discord.HTTPException):
        return None
    return role


# --- individual events. each returns (title, body) or None to be skipped ---

async def ev_windfall(guild):
    amount = random.choice([50, 75, 100, 150])
    for uid, rec in DATA["users"].items():
        member = guild.get_member(int(uid))
        if member is not None and member.bot:
            continue
        rec["bones"] = rec.get("bones", 0) + amount
    await save_data()
    return ("💰 TREASURY MISCOUNT",
            f"My ledger is wrong. In your favour, this time.\n"
            f"**{amount} Bones** each. Do not thank me.")


async def ev_word_tax(guild):
    word, fine = random.choice(TAXED_WORDS)
    minutes = random.choice([10, 15, 20])
    DATA["law"] = {"kind": "word_tax", "word": word, "fine": fine,
                   "until": (now_utc() + timedelta(minutes=minutes)).isoformat()}
    await save_data()
    return (f"🚨 CAVE LAW #{random.randint(10, 99)}",
            f'I have outlawed "**{word}**" for **{minutes} minutes**. '
            f"It costs **{fine} Bones** now.\nI will be marking the offenders 🦴.")


async def ev_double_bones(guild):
    minutes = random.choice([20, 30])
    DATA["law"] = {"kind": "double",
                   "until": (now_utc() + timedelta(minutes=minutes)).isoformat()}
    await save_data()
    return ("📈 ECONOMIC BOOM",
            f"Bones are worth double for **{minutes} minutes**. Spend it or do not.")


async def ev_king(guild):
    pool = active_members(guild)
    if not pool:
        return None
    member = random.choice(pool)
    role = await hand_role_to(guild, KING_ROLE, 0xE0B341, member)
    if role is None:
        return None
    user_record(member.id)["crowned"] += 1
    await save_data()
    return ("👑 SUCCESSION",
            f"I have made {member.mention} **King of the Cave**.\n"
            f"It changes nothing. I remain in charge.")


async def ev_criminal(guild):
    pool = active_members(guild)
    if not pool:
        return None
    member = random.choice(pool)
    role = await hand_role_to(guild, CRIMINAL_ROLE, 0xB22222, member)
    if role is None:
        return None
    return ("🚨 WANTED",
            f"{member.mention} is a criminal. I have not decided what for.\n"
            f"Use `/accuse` if you want it made official.")


async def ev_vc_payout(guild):
    members = [m for vc in guild.voice_channels for m in vc.members if not m.bot]
    if not members:
        return None
    amount = random.choice([100, 150, 250])
    for m in members:
        user_record(m.id)["bones"] += amount
    await save_data()
    names = ", ".join(m.display_name for m in members[:8])
    more = f" and {len(members) - 8} others" if len(members) > 8 else ""
    return ("🔊 HAZARD PAY",
            f"**{amount} Bones** to those sitting in my voice channels.\n{names}{more}.")


async def ev_no_english(guild):
    minutes = 5
    return ("🗣️ LINGUISTIC EMERGENCY",
            f"English is suspended for **{minutes} minutes**.\n"
            f"Arabic, Arabizi, grunting. I will not be enforcing this.")


async def ev_observation(guild):
    title, body = random.choice(CAVE_EVENTS)
    return (title, body)



TEMP_NICKNAMES = [
    "Rock Enjoyer", "Provisional Human", "Second Best Grunter", "Under Review",
    "Fire Hazard", "Owes The Treasury", "Not The King", "Cave Intern",
    "Recently Sophisticated", "Unverified Mammal", "Rock Adjacent",
    "Emotional Support Troglodyte", "Suspect", "Formerly Employed",
    "Acting Deputy Grunt", "Structurally Unsound",
]


async def ev_nickname(guild):
    """Rename ONE person for a while, and remember how to put it back.

    Deliberately not everyone. Restoring 121 nicknames means 121 chances to
    fail and leave somebody stuck. One is recoverable; a whole server is not.
    Returns None if the bot lacks the permission, so this simply never fires
    until the bot is re-invited with Manage Nicknames.
    """
    if not guild.me.guild_permissions.manage_nicknames:
        return None
    if (DATA.get("clock") or {}).get("nick_restore"):
        return None                                   # one at a time

    pool = [m for m in active_members(guild)
            if m != guild.owner and m.top_role < guild.me.top_role]
    if not pool:
        return None

    member = random.choice(pool)
    original = member.nick                            # None means "had no nickname"
    new = random.choice(TEMP_NICKNAMES)[:32]
    try:
        await member.edit(nick=new, reason="Troglodyte OS event")
    except (discord.Forbidden, discord.HTTPException):
        return None

    minutes = 10
    DATA.setdefault("clock", {})["nick_restore"] = {
        "user": member.id,
        "original": original,
        "at": (now_utc() + timedelta(minutes=minutes)).isoformat(),
    }
    await save_data()
    return ("📛 CLERICAL REASSIGNMENT",
            f"{member.mention} is **{new}** for **{minutes} minutes**. I have decided.")


async def restore_nicknames(guild):
    """Put a renamed member back. Safe to call repeatedly and on startup."""
    clock = DATA.setdefault("clock", {})
    pending = clock.get("nick_restore")
    if not pending:
        return
    try:
        if now_utc() < datetime.fromisoformat(pending["at"]):
            return
    except (KeyError, ValueError):
        pass                                          # malformed, restore now

    member = guild.get_member(pending.get("user", 0))
    if member is not None:
        try:
            await member.edit(nick=pending.get("original"),
                              reason="Troglodyte OS: reassignment expired")
        except (discord.Forbidden, discord.HTTPException):
            pass
    clock.pop("nick_restore", None)
    await save_data()


EVENT_POOL = [
    (ev_windfall, 2),
    (ev_word_tax, 3),
    (ev_double_bones, 2),
    (ev_king, 2),
    (ev_criminal, 2),
    (ev_vc_payout, 3),
    (ev_no_english, 1),
    (ev_nickname, 2),
    (ev_observation, 4),
]


def pick_event():
    handlers = []
    for fn, weight in EVENT_POOL:
        handlers.extend([fn] * weight)
    return random.choice(handlers)


# ---------------------------------------------------------------------------
# the roast and the prophecy
# ---------------------------------------------------------------------------

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


async def recent_words_of(guild, member, limit_channels=4):
    """Gather a member's recent messages across the busiest channels."""
    lines = []
    channels = [c for c in guild.text_channels
                if c.permissions_for(guild.me).read_message_history][:limit_channels]
    for channel in channels:
        try:
            async for message in channel.history(limit=120):
                if message.author.id != member.id or message.author.bot:
                    continue
                text = re.sub(r"https?://\S+", "[link]", message.content).strip()
                if len(text) > 3:
                    lines.append(text[:180])
                if len(lines) >= 20:
                    break
        except (discord.Forbidden, discord.HTTPException):
            continue
        if len(lines) >= 20:
            break
    lines.reverse()
    return lines


# ---------------------------------------------------------------------------
# background theatre
# ---------------------------------------------------------------------------

def _event_channel():
    if EVENT_CHANNEL:
        return bot.get_channel(int(EVENT_CHANNEL))
    return None


async def daily_stage():
    """Today's thread. Everything I say goes in it, so the assembly stays
    readable and every day I have spoken is still there to be read back."""
    channel = _event_channel()
    if channel is None:
        return None

    today = local_today()
    clock = DATA.setdefault("clock", {})
    stage = clock.get("stage") or {}

    if stage.get("date") == today and stage.get("id"):
        thread = channel.guild.get_thread(int(stage["id"]))
        if thread is None:
            try:
                thread = await bot.fetch_channel(int(stage["id"]))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                thread = None
        if thread is not None:
            if getattr(thread, "archived", False):
                try:
                    await thread.edit(archived=False)
                except discord.HTTPException:
                    pass
            return thread

    label = local_now().strftime("%d %B")
    if label.startswith("0"):
        label = label[1:]
    try:
        anchor = await channel.send(
            f"## \U0001f5ff THE CAVE, {label.upper()}\n"
            f"Everything I say today is in the thread below.")
        thread = await anchor.create_thread(name=f"\U0001f5ff {label}",
                                            auto_archive_duration=10080)
    except (discord.Forbidden, discord.HTTPException) as exc:
        print(f"[!] could not open today's thread: {exc}")
        return channel

    clock["stage"] = {"date": today, "id": thread.id}
    await save_data()
    return thread


def local_now():
    """Cave time. The tribe is in Beirut, so that is what a day means here."""
    return now_utc().astimezone(CAVE_TZ)


def local_today():
    return local_now().strftime("%Y-%m-%d")


def _due(key, minutes=None, daily=False):
    """Has this scheduled thing come round yet? Survives restarts.

    Daily things wait for DAILY_HOUR in Beirut. Before that they are not due,
    so a restart at 3am does not fire the whole day's output at 3am."""
    clock = DATA.setdefault("clock", {})
    now = now_utc()
    if daily:
        here = local_now()
        if here.hour < DAILY_HOUR:
            return False
        return clock.get(key) != here.strftime("%Y-%m-%d")
    stamp = clock.get(key)
    if stamp:
        try:
            if now < datetime.fromisoformat(stamp):
                return False
        except ValueError:
            pass
    clock[key] = (now + timedelta(minutes=minutes)).isoformat()
    return True


@tasks.loop(minutes=5)
async def cave_events():
    """Fires an event every 30 to 60 minutes, at an unpredictable moment."""
    channel = _event_channel()
    if channel is None:
        return
    await restore_nicknames(channel.guild)      # runs every tick, not just on event
    if not _due("next_event", minutes=random.randint(30, 60)):
        return
    await save_data()

    result = None
    for _ in range(3):                      # some events no-op (empty VC, etc)
        handler = pick_event()
        try:
            result = await handler(channel.guild)
        except Exception as exc:            # never let one bad event kill the loop
            print(f"[!] event {handler.__name__} failed: {exc}")
            result = None
        if result:
            break
    if not result:
        return

    title, body = result
    embed = discord.Embed(title=title, description=body, colour=0xB22222)
    stage = await daily_stage() or channel
    try:
        await stage.send(embed=embed)
    except discord.HTTPException:
        pass


@cave_events.before_loop
async def _before_events():
    await bot.wait_until_ready()
    await asyncio.sleep(30)


@tasks.loop(minutes=10)
async def daily_roast():
    """One roast a day, of someone who has actually been talking."""
    channel = _event_channel()
    if channel is None or not GEMINI_KEY:
        return
    if not _due("last_roast", daily=True):
        return

    pool = active_members(channel.guild, exclude_exempt=True)
    if not pool:
        return
    member = random.choice(pool)
    lines = await recent_words_of(channel.guild, member)
    if len(lines) < 5:
        return

    try:
        roast = await ask_gemini(ROAST_PROMPT.format(
            name=member.display_name, transcript="\n".join(lines)))
    except RuntimeError as exc:
        print(f"[!] roast skipped: {exc}")
        return

    DATA.setdefault("clock", {})["last_roast"] = local_today()
    await save_data()

    embed = discord.Embed(
        title="🏛️ THE DAILY INSULT",
        description=f"Today's subject: {member.mention}\n\n{roast.strip()[:1500]}",
        colour=0x8B0000,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Opt out any time with the {ROAST_EXEMPT_ROLE} role.")
    stage = await daily_stage() or channel
    try:
        await stage.send(embed=embed)
    except discord.HTTPException:
        pass


@daily_roast.before_loop
async def _before_roast():
    await bot.wait_until_ready()


@tasks.loop(minutes=10)
async def daily_prophecy():
    channel = _event_channel()
    if channel is None or not GEMINI_KEY:
        return
    if not _due("last_prophecy", daily=True):
        return
    try:
        text = await ask_gemini(PROPHECY_PROMPT)
    except RuntimeError as exc:
        print(f"[!] prophecy skipped: {exc}")
        return

    text = text.strip()[:1200]
    clock = DATA.setdefault("clock", {})
    clock["last_prophecy"] = local_today()
    clock["prophecy_text"] = text
    await save_data()

    embed = discord.Embed(title="🔮 THE CAVE HAS SPOKEN", description=text, colour=0x4B0082)
    embed.set_footer(text="Offer a reading with /interpret")
    stage = await daily_stage() or channel
    try:
        await stage.send(embed=embed)
    except discord.HTTPException:
        pass


@daily_prophecy.before_loop
async def _before_prophecy():
    await bot.wait_until_ready()


@tasks.loop(minutes=TRIVIA_TOPUP_EVERY)
async def restock_the_bank():
    """Deepens the shelves while nobody is looking, one subject at a time, so that
    by the time anyone presses a button there is already a queue waiting."""
    if not GEMINI_KEYS:
        return
    pools = DATA.setdefault("trivia", {}).setdefault("pool", {})
    thin = [(len(pools.get(pool_key(key, level), [])), key, level)
            for key, _label, _emoji in TRIVIA_CATEGORIES
            for level in TRIVIA_LEVELS]
    thin = [row for row in thin if row[0] < TRIVIA_POOL_TARGET]
    if not thin:
        return
    thin.sort()                                  # the emptiest shelf first
    _count, topic_key, level = thin[0]
    try:
        got = await stock_pool(topic_key, level)
        if got:
            print(f"[+] banked {got} for {topic_key}/{level} "
                  f"({len(pools.get(pool_key(topic_key, level), []))} on the shelf)")
    except Exception as exc:  # noqa: BLE001
        print(f"[!] restock {topic_key}/{level}: {exc}")


@restock_the_bank.before_loop
async def _restock_waits():
    await bot.wait_until_ready()


@tasks.loop(minutes=10)
async def daily_question():
    channel = _event_channel()
    if channel is None:
        return
    if not _due("last_question", daily=True):
        return
    question = random.choice(DAILY_QUESTIONS)
    embed = discord.Embed(
        title="🧠 TODAY'S PHILOSOPHICAL QUESTION",
        description=question,
        colour=0x4B0082,
    )
    embed.set_footer(text="The assembly will now deliberate. Badly.")
    DATA.setdefault("clock", {})["last_question"] = local_today()
    await save_data()
    stage = await daily_stage() or channel
    try:
        message = await stage.send(embed=embed)
        for emoji in ("🟢", "🔴", "🪨"):
            await message.add_reaction(emoji)
    except discord.HTTPException:
        pass


@daily_question.before_loop
async def _before_daily():
    await bot.wait_until_ready()


# ---------------------------------------------------------------------------

def main():
    if not TOKEN:
        raise SystemExit(
            "No DISCORD_TOKEN found.\n"
            "Create a .env file next to this script containing:\n"
            "    DISCORD_TOKEN=your-token-here\n"
            "    GUILD_ID=338649070904016898\n"
        )
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
