import discord
from discord.ext import commands


async def convert_prefix(ctx, value):
    if len(value) > 5:
        raise commands.BadArgument('Sorry! the prefix cannot be longer than 5 characters')

    return value


async def convert_giveawayrole(ctx, value):
    role = await commands.RoleConverter().convert(ctx, value)
    return role.id


async def convert_reset(ctx, value):
    value = value.strip().lower()
    conf = next((c for c in CONFIGURATIONS if value == c['name']), None)
    if not conf:
        raise commands.BadArgument('Could not find that configuration.. Try again')
    return None


CONFIGURATIONS = [
    {
        "title": "Bot Prefix",
        "name": "prefix",
        "description": "Set a custom prefix for this bot",
        "example": "`{0}config prefix !`",
        "convert": convert_prefix
    },
    {
        "title": "Giveaway Role",
        "name": "giveawayrole",
        "description": "If any member has this role, they will be able to host giveaways in your server, otherwise it requires `ADMINISTRATOR` permissions",
        "example": "`{0}config giveawayrole @giveaways`",
        "convert": convert_giveawayrole
    },
    {
        "title": "Reset",
        "name": "reset",
        "description": "Resets a configuration to its default",
        "example": "`{0}config reset prefix`",
        "convert": convert_reset
    }
]

class ConfigCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_permissions(embed_links=True)
    @commands.command(aliases=['config'])
    async def conf(self, ctx: commands.Context, key=None, *, value=None):
        conf = None
        if key:
            key = key.strip().lower()
            conf = next((c for c in CONFIGURATIONS if key == c['name']), None)
        
        if conf:
            if value:
                converted = await conf['convert'](ctx, value)
                if converted:
                    await ctx.update_config({conf['name']: converted})
                    return await ctx.send(f"Successfully set the **{conf['title']}** to `{converted}`")
                else: 
                    key = value.strip().lower()
                    await ctx.update_config({key: None})
                    return await ctx.send(f"Successfully reset the **{key}**")

            config = ctx.get_config()
            current = config.get(conf['name'], 'None')
            embed = discord.Embed(
                title=conf['title'],
                description=conf['description']
            )
            embed.add_field(name="Current Setting", value=f"`{current}`", inline=False)
            embed.add_field(name="Example", value=conf['example'].format(ctx.prefix), inline=False)
            return await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Configuration",
                description=f"Use `{ctx.prefix}config <key>` to see more details about the configuration"
            )
            for conf in CONFIGURATIONS:
                embed.add_field(name=conf['title'], value=f"`{ctx.prefix}config {conf['name']}`")
            
            return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ConfigCog(bot))