from datetime import datetime
import time as timer
import platform

import discord
import psutil
from discord.ext import commands

from .utils import utils, time


class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()

    @commands.command()
    async def ping(self, ctx):
        """Shows the bot latency"""
        start = timer.perf_counter()
        message = await ctx.send("Ping...")
        end = timer.perf_counter()

        duration = round((end - start) * 1000, 2)
        heartbeat = round(self.bot.latency * 1000, 2)
        await message.edit(content=f'**Pong!** Roundtrip: `{duration}ms`, Heartbeat: `{heartbeat}ms`')
    
    @commands.command()
    async def invite(self, ctx):
        """Add me to your discord server"""
        embed = discord.Embed(
            title="Invite",
            description=f"To add **{self.bot}** to your guild, use the following link\n{self.bot.invite}"
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def stats(self, ctx):
        """Shows you bot statistics"""
        uptime = time.friendly_duration(datetime.utcnow() - self.bot.uptime, long=True)
        memory_usage = self.process.memory_full_info().uss / 1024**2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        guilds = members = 0

        for guild in self.bot.guilds:
            guilds += 1
            members += guild.member_count

        embed = discord.Embed()
        embed.title = 'Bot Statistics'
        embed.timestamp = datetime.utcnow()
        embed.description = utils.codeblock("\n".join([
            f"• Version      :: {self.bot.version}",
            f"• Uptime       :: {uptime}",
            f"• Users        :: {len(self.bot.users)}",
            f"• Guilds       :: {len(self.bot.guilds)}",
            f"• Discord.py   :: {discord.__version__}",
            f"• Python       :: {platform.python_version()}",
            f"• Memory Usage :: {memory_usage} MiB",
            f"• CPU Usage    :: {cpu_usage}%"
        ]), 'asciidoc')

        embed.add_field(name="Invite", value="[Click Here]()")
        embed.add_field(name="Support", value="[Click Here]()")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(GeneralCog(bot))