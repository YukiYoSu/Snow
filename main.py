import random
import asyncio
import discord
from discord.ext import commands
from keep_alive import keep_alive
from islands import generate_island
from kraken import increase_threat, get_threat_level, decrease_threat, time_since_last_message
import os
import json
import time

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ADMINS = [1351629934984040549, 1385968704558465024]
DRUNK_USERS = {}  # user_id: expire_time

CONFIG_FILE = "pirate_config.json"
PROGRESS_FILE = "progress.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def set_broadcast_channel(guild_id, channel_id):
    config = load_config()
    config[str(guild_id)] = channel_id
    save_config(config)

def get_broadcast_channel(guild_id):
    config = load_config()
    return config.get(str(guild_id))

def load_progress():
    try:
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

async def send_pirate_broadcast(guild, message):
    channel_id = get_broadcast_channel(guild.id)
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(message)

def whirlpool_encounter():
    riddles = [
        {"question": "I have seas with no water, coasts with no sand, towns without people. What am I?", "answer": "map"},
        {"question": "What has a bottom at the top?", "answer": "leg"},
        {"question": "The more you take, the more you leave behind. What am I?", "answer": "footsteps"}
    ]
    return random.choice(riddles)

def pirateify(text):
    slurred = text.replace("s", "sh").replace("r", "rr").replace("you", "ye").replace("my", "me")
    endings = [" Arrr!", " *hic*", " Yo-ho-ho!", " 🍻", " Aye aye!"]
    return slurred + random.choice(endings)

# === COMMANDS ===

@bot.command(name="tavern")
async def tavern(ctx):
    user_id = ctx.author.id
    DRUNK_USERS[user_id] = time.time() + 120  # 2 minutes drunk
    await ctx.send("🍻 You drink deeply from a mug of grog... you're feelin' it now, matey!")

@bot.command(name="whirlpool")
async def whirlpool_command(ctx):
    chance = random.randint(1, 8)
    if chance == 1:
        riddle = whirlpool_encounter()
        await ctx.send(
            f"🌀 **Whirlpool Encounter!** You're caught in swirling seas!\n\nSolve this to escape:\n**{riddle['question']}**\n\nReply with your answer."
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower().strip() == riddle["answer"]:
                await ctx.send("✅ You escape the whirlpool and find a treasure chest!")
            else:
                await ctx.send("❌ Wrong answer! You barely escape with your life.")
        except asyncio.TimeoutError:
            await ctx.send("⏳ You didn't answer in time. The whirlpool spits you out—drenched and dazed.")
    else:
        await ctx.send("🌊 You sail safely through calm waters.")

@bot.command(name="setpiratechannel")
@commands.has_permissions(manage_guild=True)
async def set_pirate_channel(ctx):
    set_broadcast_channel(ctx.guild.id, ctx.channel.id)
    await ctx.send("📻 Pirate Radio broadcasts will now appear in this channel.")

@bot.command(name="broadcast")
async def broadcast(ctx, *, message: str):
    if ctx.author.id not in ADMINS:
        await ctx.send("🛑 You are not authorized to use pirate radio.")
        return

    broadcast_msg = f"📡 **PIRATE RADIO BROADCAST** 📡\n🏴‍☠️ `{ctx.author.display_name}` shouts from the crow's nest:\n\n{message}"
    sent = 0
    for guild in bot.guilds:
        try:
            await send_pirate_broadcast(guild, broadcast_msg)
            sent += 1
        except:
            continue

    await ctx.send(f"📡 Broadcast sent to {sent} server(s).")

@bot.command(name="explore")
async def explore(ctx):
    user_id = str(ctx.author.id)
    island = generate_island()

    progress = load_progress()
    if user_id not in progress:
        progress[user_id] = []

    if island not in progress[user_id]:
        progress[user_id].append(island)
        save_progress(progress)
        await ctx.send(f"🏝️ **New island discovered!**\n{island}")
    else:
        await ctx.send(f"🏝️ You revisit a familiar island:\n{island}")

@bot.command(name="progress")
async def progress(ctx):
    user_id = str(ctx.author.id)
    progress = load_progress()
    discovered = len(progress.get(user_id, []))
    await ctx.send(f"🗺️ You have discovered **{discovered}** unique island(s)!")

# === BACKGROUND TASK ===
async def kraken_decay_loop():
    await bot.wait_until_ready()
    print("Kraken decay loop started")
    while not bot.is_closed():
        idle_seconds = time_since_last_message()
        print(f"[Kraken Monitor] Idle time: {idle_seconds:.2f}s | Threat: {get_threat_level()}")

        if idle_seconds >= 60:
            channel = None
            for guild in bot.guilds:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        break
                if channel:
                    break

            if channel:
                previous = get_threat_level()
                decrease_threat(5)
                current = get_threat_level()

                if previous > 0 and current == 0:
                    await channel.send("💤 The Kraken sinks into slumber... the sea calms.")
                elif current > 0:
                    await channel.send(f"🌊 The Kraken's rage fades slightly... Threat level: {current}/100")

        await asyncio.sleep(60)

# === EVENTS ===
@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")
    bot.loop.create_task(kraken_decay_loop())

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    if user_id in DRUNK_USERS and DRUNK_USERS[user_id] > time.time():
        pirate_message = pirateify(message.content)
        await message.channel.send(f"🥴 {message.author.display_name} (drunk): {pirate_message}")
        return
    elif user_id in DRUNK_USERS:
        del DRUNK_USERS[user_id]

    triggered = increase_threat(2)
    if triggered:
        await message.channel.send("🐙 **THE KRAKEN AWAKENS!** The sea roars as tentacles rise from the deep!")
    else:
        level = get_threat_level()
        if level > 0 and level % 20 == 0:
            await message.channel.send(f"🌊 The Kraken stirs... Threat level: {level}/100")

    await bot.process_commands(message)

# === START ===
keep_alive()
bot.run(os.getenv("TOKEN"))
