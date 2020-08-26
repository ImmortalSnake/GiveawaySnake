import time
import traceback

import discord
from discord.ext import commands
from .utils import utils


class AdminCog(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return await self.bot.is_owner(ctx.author)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    @commands.command()
    async def load(self, ctx: commands.Context, *, module: str):
        """Loads a given extension"""
        try:
            self.bot.load_extension(module)
        except Exception as err:
            await ctx.send(f'{err.__class__.__name__}: {err}')
        else:
            await ctx.send(f'Successfully loaded module **{module}**')

    @commands.command()
    async def unload(self, ctx: commands.Context, *, module: str):
        """Unloads a given extension"""
        try:
            self.bot.unload_extension(module)
        except Exception as err:
            await ctx.send(f'{err.__class__.__name__}: {err}')
        else:
            await ctx.send(f'Successfully unloaded module **{module}**')

    @commands.command()
    async def reload(self, ctx: commands.Context, *, module: str):
        """Reloads a given extension"""
        try:
            self.bot.reload_extension(module)
        except Exception as err:
            await ctx.send(f'{err.__class__.__name__}: {err}')
        else:
            await ctx.send(f'Successfully reloaded module **{module}**')

    @commands.command()
    async def shutdown(self, ctx: commands.Context):
        """Closes discord connection and shuts the bot down"""
        await ctx.send('Shutting down...')
        await self.bot.logout()

    @commands.command(name="eval")
    async def _eval(self, ctx: commands.Context, *, inp: str):
        """Evaluates python code"""
        code = '\n'.join(f'    {l}' for l in self.cleanup_code(inp).splitlines())
        env = {
            'ctx': ctx,
            'bot': self.bot,
            'discord': discord,
            'commands': commands,
            'message': ctx.message
        }

        env.update(globals())
        body = f"async def func():\n{code}"

        try:
            exec(body, env)
        except Exception as e:
            print(traceback.format_exc())
            return await ctx.send(utils.codeblock(f'{e.__class__.__name__}: {e}', 'py'))

        try:
            start = time.perf_counter()
            result = await env['func']()
            end = time.perf_counter()
        except Exception as e:
            return await ctx.send(utils.codeblock(f'{e.__class__.__name__}: {e}', 'py'))

        await ctx.send(
            f"**Result**:\n{utils.codeblock(result, 'py')}\n"
            f"**Type**:\n{utils.codeblock(type(result), 'py')}\n"
            f"**Time**:\n`{round((end-start)*1000, 5)} ms`"
        )


def setup(bot):
    bot.add_cog(AdminCog(bot))
