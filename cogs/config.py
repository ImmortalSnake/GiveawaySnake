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
        "example": "`{0}config prefix !`\n`{0}config reset prefix`",
        "default": "m!",
        "convert": convert_prefix
    },
    {
        "title": "Giveaway Role",
        "name": "giveawayrole",
        "description": "If any member has this role, they will be able to host giveaways in your server, otherwise it requires `ADMINISTRATOR` permissions",
        "example": "`{0}config giveawayrole @giveaways`\n`{0}config reset giveawayrole`",
        "convert": convert_giveawayrole
    }
]

class ConfigCog(commands.Cog, name="⚙️ Config Commands"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_permissions(embed_links=True)
    @commands.group(invoke_without_command=True, aliases=['config'])
    async def conf(self, ctx: commands.Context, key=None, *, value=None):
        "Manage your server configuration"
        conf = None
        if key:
            key = key.strip().lower()
            conf = next((c for c in CONFIGURATIONS if c['name'] == key), None)
        
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

    @conf.command()
    async def reset(self, ctx, *, value=''):
        value = value.strip().lower()
        conf = next((c for c in CONFIGURATIONS if c['name'] == value), None)
        if not conf:
            raise commands.BadArgument('Could not find that configuration.. Try again')

        await ctx.update_config({value: conf.get('default')})
        return await ctx.send(f"Successfully reset the **{conf['title']}**")


def setup(bot):
    bot.add_cog(ConfigCog(bot))