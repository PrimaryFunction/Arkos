import discord
from discord.ext import commands
import sqlite3

class XPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect("xp.db")
        self.cursor = self.db.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS xp (
                user_id TEXT PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )''')
        self.db.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        # Only give XP if the message was sent by the proxysay webhook (bot)
        if message.author.bot and message.webhook_id is not None:
            # Try to extract the user ID from the message content (proxysay should add it as a hidden marker)
            # This requires proxysay to add a marker, or you can use the display name as a fallback
            # For now, we will not be able to attribute XP to the real user unless you add a marker
            pass  # No XP awarded unless you update proxysay to add a marker
        # No XP for regular messages
        return

    def add_xp(self, user_id, channel):
        self.cursor.execute('SELECT xp, level FROM xp WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if row:
            xp, level = row
            xp += 10  # XP per proxysay
        else:
            xp, level = 10, 1
        next_level_xp = 100 * level
        if xp >= next_level_xp:
            level += 1
            asyncio.create_task(channel.send(f"<@{user_id}> leveled up to {level}!"))
        self.cursor.execute('REPLACE INTO xp (user_id, xp, level) VALUES (?, ?, ?)', (user_id, xp, level))
        self.db.commit()

    @commands.command()
    async def xp(self, ctx, member: discord.Member = None):
        """Check your or another user's XP and level."""
        member = member or ctx.author
        user_id = str(member.id)
        self.cursor.execute('SELECT xp, level FROM xp WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if row:
            xp, level = row
        else:
            xp, level = 0, 1
        await ctx.send(f"{member.display_name} - Level: {level}, XP: {xp}")

    def cog_unload(self):
        self.db.close()

async def setup(bot):
    await bot.add_cog(XPCog(bot))
    print("XPCog loaded")
