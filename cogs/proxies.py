import discord
from discord.ext import commands
import sqlite3

class ProxyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect("proxies.db")
        self.cursor = self.db.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                proxy_key TEXT PRIMARY KEY,
                proxy_name TEXT,
                avatar_url TEXT
            )''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxy_users (
                proxy_key TEXT,
                user_id TEXT,
                PRIMARY KEY (proxy_key, user_id)
            )''')
        self.db.commit()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def deleteproxy(self, ctx, key: str):
        """Delete a proxy and remove all associated users. (Admin only)"""
        self.cursor.execute('DELETE FROM proxy_users WHERE proxy_key = ?', (key,))
        self.cursor.execute('DELETE FROM proxies WHERE proxy_key = ?', (key,))
        self.db.commit()
        await ctx.send(f"Proxy '{key}' and all associated access have been deleted.")

    @commands.command()
    async def createproxy(self, ctx, key: str, name: str, avatar_url: str):
        """Create a proxy with a unique key."""
        try:
            self.cursor.execute('INSERT INTO proxies (proxy_key, proxy_name, avatar_url) VALUES (?, ?, ?)',
                                (key, name, avatar_url))
            self.cursor.execute('INSERT INTO proxy_users (proxy_key, user_id) VALUES (?, ?)',
                                (key, str(ctx.author.id)))
            self.db.commit()
            await ctx.send(f"Proxy '{name}' created with key '{key}'")
        except sqlite3.IntegrityError:
            await ctx.send("That proxy key already exists.")

    @commands.command()
    async def grantproxy(self, ctx, key: str, member: discord.Member):
        """Grant another user access to a proxy you created."""
        self.cursor.execute('SELECT * FROM proxy_users WHERE proxy_key = ? AND user_id = ?',
                            (key, str(ctx.author.id)))
        if not self.cursor.fetchone():
            await ctx.send("You do not have access to this proxy.")
            return

        self.cursor.execute('REPLACE INTO proxy_users (proxy_key, user_id) VALUES (?, ?)',
                            (key, str(member.id)))
        self.db.commit()
        await ctx.send(f"Granted access to {member.mention} for proxy '{key}'")

    @commands.command()
    async def proxysay(self, ctx, key: str, *, message: str):
        """Send a message using a proxy key. Works in threads and forum posts."""
        self.cursor.execute('SELECT * FROM proxy_users WHERE proxy_key = ? AND user_id = ?',
                            (key, str(ctx.author.id)))
        if not self.cursor.fetchone():
            await ctx.send("You do not have access to this proxy.")
            return

        self.cursor.execute('SELECT proxy_name, avatar_url FROM proxies WHERE proxy_key = ?', (key,))
        row = self.cursor.fetchone()

        if not row:
            await ctx.send("Proxy not found.")
            return

        name, avatar_url = row
        # Determine the parent channel for threads and forum posts
        channel = ctx.channel
        if hasattr(channel, 'parent') and channel.parent is not None:
            parent = channel.parent
            # If this is a thread or forum post, use the parent channel to create the webhook
            webhook_channel = parent
        else:
            webhook_channel = channel

        webhook = await webhook_channel.create_webhook(name=name)
        await webhook.send(message, username=name, avatar_url=avatar_url, thread=channel if hasattr(channel, 'parent') and channel.parent is not None else None)
        await webhook.delete()
        await ctx.message.delete()

    @commands.command()
    async def listproxies(self, ctx):
        """List all proxies you have access to."""
        self.cursor.execute('''
            SELECT proxies.proxy_key, proxies.proxy_name FROM proxies
            JOIN proxy_users ON proxies.proxy_key = proxy_users.proxy_key
            WHERE proxy_users.user_id = ?
        ''', (str(ctx.author.id),))
        proxies = self.cursor.fetchall()
        if not proxies:
            await ctx.send("You don't have access to any proxies.")
        else:
            msg = "Your proxies:\n" + "\n".join([f"Key: {key}, Name: {name}" for key, name in proxies])
            await ctx.send(msg)

    def cog_unload(self):
        self.db.close()


async def setup(bot):
    await bot.add_cog(ProxyCog(bot))
    print("ProxyCog loaded")