import os
import discord
from discord.ext import commands
from discord import app_commands

import sqlite3
import logging
from . import xp

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

    @app_commands.command(name="deleteproxy", description="Delete a proxy and remove all associated users. (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def deleteproxy_slash(self, interaction: discord.Interaction, key: str):
        self.cursor.execute('DELETE FROM proxy_users WHERE proxy_key = ?', (key,))
        self.cursor.execute('DELETE FROM proxies WHERE proxy_key = ?', (key,))
        self.db.commit()
        await interaction.response.send_message(f"Proxy '{key}' and all associated access have been deleted.")

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

    @app_commands.command(name="grantproxy", description="Grant another user access to a proxy you created.")
    async def grantproxy_slash(self, interaction: discord.Interaction, key: str, member: discord.Member):
        self.cursor.execute('SELECT * FROM proxy_users WHERE proxy_key = ? AND user_id = ?',
                            (key, str(interaction.user.id)))
        if not self.cursor.fetchone():
            await interaction.response.send_message("You do not have access to this proxy.", ephemeral=True)
            return

        self.cursor.execute('REPLACE INTO proxy_users (proxy_key, user_id) VALUES (?, ?)',
                            (key, str(member.id)))
        self.db.commit()
        await interaction.response.send_message(f"Granted access to {member.mention} for proxy '{key}'")

    @commands.command()
    async def listproxies(self, ctx):
        """List all proxies you have access to, each as an embed with thumbnail and access list."""
        self.cursor.execute('''
            SELECT proxies.proxy_key, proxies.proxy_name, proxies.avatar_url FROM proxies
            JOIN proxy_users ON proxies.proxy_key = proxy_users.proxy_key
            WHERE proxy_users.user_id = ?
        ''', (str(ctx.author.id),))
        proxies = self.cursor.fetchall()
        if not proxies:
            await ctx.send("You don't have access to any proxies.")
        else:
            for key, name, avatar_url in proxies:
                # Get all users with access to this proxy
                self.cursor.execute('SELECT user_id FROM proxy_users WHERE proxy_key = ?', (key,))
                user_ids = [row[0] for row in self.cursor.fetchall()]
                members = [ctx.guild.get_member(int(uid)) for uid in user_ids]
                member_mentions = [m.mention for m in members if m]
                access_list = ", ".join(member_mentions) if member_mentions else "No users found"
                embed = discord.Embed(title=f"Proxy: {name}", description=f"Key: {key}\nAccess: {access_list}")
                if avatar_url:
                    embed.set_thumbnail(url=avatar_url)
                await ctx.send(embed=embed)

    @app_commands.command(name="listproxies", description="List all proxies you have access to.")
    async def listproxies_slash(self, interaction: discord.Interaction):
        self.cursor.execute('''
            SELECT proxies.proxy_key, proxies.proxy_name, proxies.avatar_url FROM proxies
            JOIN proxy_users ON proxies.proxy_key = proxy_users.proxy_key
            WHERE proxy_users.user_id = ?
        ''', (str(interaction.user.id),))
        proxies = self.cursor.fetchall()
        if not proxies:
            await interaction.response.send_message("You don't have access to any proxies.", ephemeral=True)
        else:
            for key, name, avatar_url in proxies:
                # Get all users with access to this proxy
                self.cursor.execute('SELECT user_id FROM proxy_users WHERE proxy_key = ?', (key,))
                user_ids = [row[0] for row in self.cursor.fetchall()]
                members = [interaction.guild.get_member(int(uid)) for uid in user_ids]
                member_mentions = [m.mention for m in members if m]
                access_list = ", ".join(member_mentions) if member_mentions else "No users found"
                embed = discord.Embed(title=f"Proxy: {name}", description=f"Key: {key}\nAccess: {access_list}")
                if avatar_url:
                    embed.set_thumbnail(url=avatar_url)
                await interaction.channel.send(embed=embed)
            await interaction.response.send_message("Proxies listed above.", ephemeral=True)

    def cog_unload(self):
        self.db.close()

async def setup(bot):
    cog = ProxyCog(bot)
    await bot.add_cog(cog)
    guild_id = int(os.getenv("GUILD_ID"))
    guild_obj = discord.Object(id=guild_id)
    # Manually add each app command to the tree for your guild
    bot.tree.add_command(cog.listproxies_slash, guild=guild_obj)
    bot.tree.add_command(cog.grantproxy_slash, guild=guild_obj)
    bot.tree.add_command(cog.deleteproxy_slash, guild=guild_obj)
    print("ProxyCog loaded and slash commands registered")