import discord
from discord.ext import commands

import os
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # Enable if you need message content

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def main():
    # Load all cogs in the cogs directory except __init__.py
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())