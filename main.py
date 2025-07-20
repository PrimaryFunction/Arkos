import discord
from discord.ext import commands
from discord import app_commands

import os
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # Make sure to add your GUILD_ID to the .env file

# Add discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)  # Sync all app_commands (slash commands) to your guild
    await bot.tree.clear_commands(guild=None)

async def main():
    # Load all cogs in the cogs directory except __init__.py
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())