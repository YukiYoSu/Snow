import discord
from discord.ext import commands
from keep_alive import keep_alive
from islands import generate_island
from kraken import increase_threat, get_threat_level
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")

@bot.command(name="explore")
async def explore(ctx):
    island = generate_island()
    await ctx.send(island)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    triggered = increase_threat(2)
    if triggered:
        await message.channel.send("🐙 **THE KRAKEN AWAKENS!**")
    else:
        level = get_threat_level()
        if level % 20 == 0:
            await message.channel.send(f"🌊 The Kraken stirs... Threat level: {level}/100")
    await bot.process_commands(message)

keep_alive()
bot.run(os.getenv("TOKEN"))
