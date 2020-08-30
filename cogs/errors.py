import discord
from discord.ext import commands


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        ignore = [commands.NotOwner, commands.CommandNotFound]
        if type(err) in ignore:
            return
    
        elif type(err) == commands.MissingPermissions:
            missing = ', '.join([f'`{p}`' for p in err.missing_perms])
            await ctx.send(f"❌ Sorry, but you need {missing} permission(s) to use this command")
    
        elif type(err) == commands.BotMissingPermissions:
            missing = ', '.join([f'`{p}`' for p in err.missing_perms])
            await ctx.send(f"❌ Sorry, but I need {missing} permission(s) to use this command")
        
        elif type(err) == commands.CheckFailure:
            await ctx.send("❌ Sorry, you cannot use this command")

        else:
            await ctx.send(err)


def setup(bot):
    bot.add_cog(Errors(bot))
