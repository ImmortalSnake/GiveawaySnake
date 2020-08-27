import discord
from discord.ext import commands


async def convert_prefix(ctx, value):
    if len(value) > 5:
        raise commands.BadArgument('Sorry! the prefix cannot be longer than 5 characters')

    return value


async def convert_giveawayrole(ctx, value):
    role = await commands.RoleConverter().convert(ctx, value)
    return role.id


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
    }
]

class ConfigCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.command(aliases=['config'])
    async def conf(self, ctx: commands.Context, key=None, *, value=None):
        conf = None
        if key:
            key = key.strip().lower()
            conf = next((c for c in CONFIGURATIONS if key == c['name']), None)
        
        if conf:
            if value:
                converted = await conf['convert'](ctx, value)
                await ctx.update_config({conf['name']: converted})
                return await ctx.send(f"Successfully set the **{conf['title']}** to `{converted}`")

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