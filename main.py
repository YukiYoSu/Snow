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
from discord import app_commands

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ADMINS = [1351629934984040549, 1385968704558465024]  # Replace with your Discord user ID(s)

# Configuration functions
CONFIG_FILE = "pirate_config.json"

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

async def send_pirate_broadcast(guild, message):
    channel_id = get_broadcast_channel(guild.id)
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(message)

def whirlpool_encounter():
    riddles = [
        {
            "question": "I have seas with no water, coasts with no sand, towns without people. What am I?",
            "answer": "map"
        },
        {
            "question": "What has a bottom at the top?",
            "answer": "leg"
        },
        {
            "question": "The more you take, the more you leave behind. What am I?",
            "answer": "footsteps"
        }
    ]
    return random.choice(riddles)

# Commands
@bot.command(name="setpiratechannel")
@commands.has_permissions(manage_guild=True)
async def set_pirate_channel(ctx):
    set_broadcast_channel(ctx.guild.id, ctx.channel.id)
    await ctx.send(f"📻 Pirate Radio broadcasts will now appear in this channel.")

@bot.tree.command(name="whirlpool", description="Encounter a mysterious whirlpool!")
async def whirlpool_command(interaction: discord.Interaction):
    chance = random.randint(1, 8)
    if chance == 1:
        riddle = whirlpool_encounter()
        await interaction.response.send_message(
            f"🌀 **Whirlpool Encounter!** You're caught in swirling seas!\n\nSolve this to escape:\n**{riddle['question']}**\n\nReply with your answer."
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower().strip() == riddle["answer"]:
                await interaction.followup.send("✅ You escape the whirlpool and find a treasure chest!")
            else:
                await interaction.followup.send("❌ Wrong answer! You barely escape with your life.")
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ You didn't answer in time. The whirlpool spits you out—drenched and dazed.")
    else:
        await interaction.response.send_message("🌊 You sail safely through calm waters.")

@bot.tree.command(name="broadcast", description="Send a pirate radio broadcast to the server.")
@app_commands.describe(message="Your broadcast message to all servers.")
async def pirate_broadcast(interaction: discord.Interaction, message: str):
    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("🛑 You are not authorized to use pirate radio.", ephemeral=True)
        return

    broadcast_msg = f"📡 **PIRATE RADIO BROADCAST** 📡\n🏴‍☠️ `{interaction.user.display_name}` shouts from the crow's nest:\n\n{message}"

    sent = 0
    for guild in bot.guilds:
        try:
            await send_pirate_broadcast(guild, broadcast_msg)
            sent += 1
        except:
            continue

    await interaction.response.send_message(f"📡 Broadcast sent to {sent} server(s).")

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
    island = generate_island()
    await ctx.send(island)

# Background task
async def kraken_decay_loop():
    await bot.wait_until_ready()
    print("Kraken decay loop started")
    while not bot.is_closed():
        idle_seconds = time_since_last_message()
        print(f"[Kraken Monitor] Idle time: {idle_seconds:.2f}s | Threat: {get_threat_level()}")

        if idle_seconds >= 60:
            # Find the first text channel the bot can send messages to
            channel = None
            for guild in bot.guilds:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        break
                if channel:
                    break

            if channel:
                # Fixed logic to check and message on sleep
                previous = get_threat_level()
                decrease_threat(5)
                current = get_threat_level()

                if previous > 0 and current == 0:
                    await channel.send("💤 The Kraken sinks into slumber... the sea calms.")
                elif current > 0:
                    await channel.send(f"🌊 The Kraken's rage fades slightly... Threat level: {current}/100")

        await asyncio.sleep(60)

# Events
@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")
    bot.loop.create_task(kraken_decay_loop())

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    triggered = increase_threat(2)
    if triggered:
        await message.channel.send("🐙 **THE KRAKEN AWAKENS!** The sea roars as tentacles rise from the deep!")
    else:
        level = get_threat_level()
        if level > 0 and level % 20 == 0:
            await message.channel.send(f"🌊 The Kraken stirs... Threat level: {level}/100")

    await bot.process_commands(message)

# Start the bot
keep_alive()
bot.run(os.getenv("TOKEN"))
