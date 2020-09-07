from datetime import datetime
import time as timer
import platform

import discord
import psutil
from discord.ext import commands

from .utils import utils, time


class GeneralCog(commands.Cog, name="💬 General Commands"):
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
        await ctx.send(f"To add **{self.bot.user.name}** to your guild, use the following link\n{self.bot.invite}")

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

        embed.add_field(name="Invite", value=f"[`Click Here`]({self.bot.invite})")
        embed.add_field(name="Support", value=f"[`Click Here`]({self.bot.support})")

        await ctx.send(embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @commands.command()
    async def help(self, ctx: commands.Context, *, cmd=''):
        "Displays all commands available, and shows information for each command"
        cmd = cmd.lower().strip()
        command = next((c for c in self.bot.commands if cmd == c.name or cmd in c.aliases), None)
        if not command:
            fields = {}
            embed = discord.Embed(
                title="Help",
                description=f"Displaying all commands available, use `{ctx.prefix}help <command>` to view more info in each command"
            )
            for command in self.bot.commands:
                if not command.enabled or command.hidden:
                    continue

                cogname = command.cog.qualified_name
                if cogname in fields:
                    fields[cogname] += f'`{command}` '
                else:
                    fields[cogname] = f'`{command}` '

            for cog, cmds in fields.items():
                embed.add_field(name=cog, value=cmds, inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"Command Help - {command.name.title()}",
                description=f'**{command.help}**'
            )
            embed.add_field(name='📜 | Usage', value=f'`{ctx.prefix}{command.name} {command.signature}`')
            if command.aliases:
                embed.add_field(name="📝 | Aliases", value=' '.join(f'`{a}`' for a in command.aliases), inline=False)

            await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(GeneralCog(bot))
