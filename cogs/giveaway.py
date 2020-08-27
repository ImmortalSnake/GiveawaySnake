from datetime import timedelta, datetime
import asyncio
import random

import discord
from discord.ext import commands, tasks

from .utils.time import human_duration, friendly_duration
from .utils.context import Context, PromptCancelled


async def select_winners(message: discord.Message, winner_count: int):
    """
    Selects a given amount of winners, returns None if the number of reactions
    are lesser than the required amount

    NOTE: Make sure to fetch the message first in order to cache reactions
    """
    reaction = discord.utils.get(message.reactions, emoji="🎉")
    if not reaction: return
        
    users = await reaction.users().flatten() # users is now a list of User..
    filtered = [u for u in users if type(u) == discord.Member and not u.bot]

    if len(filtered) < winner_count: return
    return random.sample(filtered, winner_count)


def winner_count(arg: str) -> int:
    "Makes sure the winner count is > 1"
    num = int(arg)
    if num < 1: 
        raise commands.BadArgument("❌ Winner count cannot be lower than 1")

    return num


def convert_duration(arg: str) -> timedelta:
    "Makes sure the giveaway duration is in the limit"
    seconds = human_duration(arg)
    if seconds < 15:
        raise commands.BadArgument("❌ Duration cannot be lesser than 15 seconds")
    elif seconds > 14 * 86400:
        raise commands.BadArgument("❌ Duration cannot be longer than 14 days")

    return timedelta(seconds=seconds)


class Giveaway(object):
    def __init__(self, bot: commands.Bot, **data):
        self.bot = bot
        self.authorID = data.get('authorID')
        self.channelID = data.get('channelID')
        self.messageID = data.get('messageID', None)
        self.title = data.get('title')
        self.endsat = data.get('endsat')
        self.winners = data.get('winners')

        self.channel = self.bot.get_channel(self.channelID)
        self.author = self.bot.get_user(self.authorID)
        self.finished = False

        self.next_refresh = self.calculate_next_refresh()

    @property
    def duration(self) -> timedelta:
        "Gives the timedelta object for the time left for the giveaway to finish"
        return self.endsat - datetime.utcnow()

    @property
    def guild(self) -> discord.Guild:
        "Returns the guild the giveaway is running in"
        return self.message.guild

    def calculate_next_refresh(self) -> timedelta:
        "Returns the datetime when the giveaway should refresh"
        time_left = self.duration.seconds
        if time_left > 24 * 3600: interval = 3 * 3600 # 3 hours at (> 1 day)
        elif time_left > 3 * 3600: interval = 3600 # 1 hour at (3 hour - 24 hour)
        elif time_left > 3600: interval = 15 * 60 # 15 minutes at (1 hour - 3hour)
        elif time_left > 20 * 60: interval = 3 * 60 # 3 minutes at (20 minutes - 1 hour)
        elif time_left > 5 * 60: interval = 60 # 1 minute at (5 minutes - 20 minutes)
        elif time_left > 30: interval = 15 # 15 seconds at (30 seconds - 5 minutes)
        else: interval = 5 # 5 seconds at (< 30 seconds)

        # now return either the time when the giveaway ends or the next refresh interval
        return min(self.endsat, datetime.utcnow() + timedelta(seconds=interval))

    def get_embed(self) -> discord.Embed:
        "Returns an embed that is displayed while the giveaway is running"
        embed = discord.Embed(title=self.title)
        embed.description = '\n'.join([
            '**React with 🎉 to enter**\n',
            f'**Winner Count:** `{self.winners}`',
            f'**Time Left:** **{friendly_duration(self.duration, long=True)}**',
            f'**Hosted By:** {self.author.mention}'
        ])
        embed.timestamp = self.endsat
        return embed.set_footer(text=f'Ends At:')
    
    async def fetch_message(self):
        "Fetches the message and caches it with the reactions"
        self.message = await self.channel.fetch_message(self.messageID)

    async def create(self) -> discord.Message:
        "Creates the giveaway message"
        embed = self.get_embed()
        self.message = await self.channel.send("🎉 **GIVEAWAY STARTED** 🎉", embed=embed)
        self.messageID = self.message.id
        return self.message

    async def refresh(self):
        "Refreshes the giveaway and edits the message with a new embed"
        self.next_refresh = self.calculate_next_refresh()
        await self.message.edit(embed=self.get_embed())

    async def finish(self):
        "Finishes the giveaway and displays the winners if any"
        self.finished = True
        embed = discord.Embed(title=self.title)
        embed.set_footer(text='Ended At:')
        embed.timestamp = datetime.utcnow()

        await self.fetch_message() # need to fetch reactions first
        winners = await select_winners(self.message, self.winners)
        if not winners:
            embed.description = f"The Giveaway has ended, not enough people voted.\n**Votes Required:** `{self.winners}`"
            await self.channel.send('❌ Could not determine a winner')
        else:
            str_winners = ', '.join(w.mention for w in winners)
            embed.description = f"**Winner(s): {str_winners}**"
            await self.channel.send(f'🎉 Congratulations {str_winners}! You won **{self.title}**\n{self.message.jump_url}')
        
        return await self.message.edit(content="🎉 **GIVEAWAY ENDED** 🎉", embed=embed)


class GiveawayNotFound(BaseException):
    pass


class GiveawayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.running = []

        self.giveaway_loop.start()

    def cog_unload(self):
        self.giveaway_loop.cancel()

    @tasks.loop(seconds=5)
    async def giveaway_loop(self):
        "This loop runs every 5 seconds and refreshes giveaways"
        now = datetime.utcnow()
        for giveaway in self.running:
            if giveaway.next_refresh <= now:
                try:
                    await self.refresh_giveaway(giveaway)
                except discord.errors.NotFound:
                    # If the channel / message is not found then delete the giveaway
                    await self.delete_giveaway(giveaway)
        
        self.running = [g for g in self.running if not g.finished]

    @giveaway_loop.before_loop
    async def before_giveaway_loop(self):
        "Loads all giveaways from database and reinitializes them"
        await self.bot.wait_until_ready()

        cursor = self.bot.db.giveaways.find() # gets all giveaways
        async for data in cursor:
            giveaway = Giveaway(self.bot, **data)
            # try fetch the message and it to running, delete if not found
            try:
                await giveaway.fetch_message()
            except discord.errors.NotFound:
                await self.delete_giveaway(giveaway)
            else:
                self.running.append(giveaway)

    async def delete_giveaway(self, giveaway: Giveaway):
        "Deletes a giveaway from the database"
        await self.bot.db.giveaways.delete_one({ 'messageID': giveaway.messageID })
        giveaway.finished = True # In order to remove it from running

    async def finish_giveaway(self, giveaway: Giveaway):
        "Finishes a giveaway and deletes it"
        await giveaway.finish()

        # This is done to quickly find which was the last giveaway ran
        # Its not necessary, but ensures that it finds the giveaway instead of looping through history
        await self.bot.db.guilds.update_one(
            {"guild": giveaway.guild.id},
            {"$set": {"lastGiveaway": giveaway.messageID}}, # if you want it can be an array to store all giveaways ran
            upsert=True
        )

        return await self.delete_giveaway(giveaway)

    async def refresh_giveaway(self, giveaway: Giveaway):
        "Refreshes a giveaway, finishes it if the time is up"
        if giveaway.finished: return
        if giveaway.endsat < datetime.utcnow(): 
            return await self.finish_giveaway(giveaway)

        return await giveaway.refresh()

    async def create_giveaway(self, **data) -> discord.Message:
        "Creates a new giveaway and saves it to the database"
        giveaway = Giveaway(self.bot, **data)
        message = await giveaway.create()
        self.running.append(giveaway)

        data.update({'messageID': message.id})
        await self.bot.db.giveaways.insert_one(data)
        return message

    def find_recent_giveaway(self, guildID: int, message: discord.Message = None) -> Giveaway:
        "Returns the giveaway with provided message or the most recent running giveaway"
        lst = [g for g in self.running if g.guild.id == guildID]
        if not lst:
            raise GiveawayNotFound("❌ There are no giveaways running in this server")

        if not message:
            giveaway = lst[-1] # recently added to the list
        else:
            giveaway = next((g for g in lst if g.messageID == message.id), None)
            if not giveaway:
                raise GiveawayNotFound("❌ Could not find that giveaway! Try again!")
        
        return giveaway

    async def cog_check(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True

        roleid = ctx.get_config().get('giveawayrole')
        return roleid and discord.utils.get(ctx.author.roles, id=roleid)

    @commands.guild_only()
    @commands.bot_has_permissions(read_message_history=True, embed_links=True, add_reactions=True)
    @commands.command()
    async def gcreate(self, ctx: Context):
        "Interactively sets up a giveaway for your server"
        try:
            channel = await ctx.prompt("Ok lets setup a giveaway for your server!\n**Which channel do you want giveaway in?**\n\nType `cancel` anytime to cancel the the giveaway", converter=commands.TextChannelConverter)
            td = await ctx.prompt(f'Nice! The giveaway will be started in {channel.mention}.\n**Now how long should the giveaway last?**', converter=convert_duration)
            winners = await ctx.prompt(f'Great! The giveaway will last for **{friendly_duration(td, True)}**\n**How many winners should be chosen?**', converter=winner_count)
            title = await ctx.prompt('Alright! **What will you be giving away?**')
            confirm = await ctx.ask(
                f'Okay, your giveaway for **{title}** in {channel.mention} will last for **{friendly_duration(td, True)}** and **{winners} winner(s)** will be chosen!\n'
                f'**Do you confirm?**'
            )
        except asyncio.TimeoutError:
            await ctx.send("❌ Sorry! you took too long to respond. Try again later!")
        except PromptCancelled:
            await ctx.send('Cancelled the giveaway!')
        else:
            if not confirm:
                return await ctx.send('Cancelled the giveaway!')
            
            endsat = datetime.utcnow() + td
            message = await self.create_giveaway(
                channelID=channel.id,
                endsat=endsat,
                winners=winners,
                authorID=ctx.author.id,
                title=title
            )
            await message.add_reaction('🎉')
            return await ctx.send(f'Done! Your giveaway has started in {channel.mention}')

    @commands.guild_only()
    @commands.bot_has_permissions(read_message_history=True, embed_links=True, add_reactions=True)
    @commands.command()
    async def gstart(self, ctx: commands.Context, td: convert_duration, winners: winner_count, *, title: str):
        "Quickly starts a giveaway in the current channel"
        endsat = datetime.utcnow() + td
        message = await self.create_giveaway(
            channelID=ctx.channel.id,
            endsat=endsat,
            winners=winners,
            authorID=ctx.author.id,
            title=title
        )
        await message.add_reaction('🎉')

    @commands.guild_only()
    @commands.bot_has_permissions(read_message_history=True, embed_links=True)
    @commands.command()
    async def gend(self, ctx: commands.Context, *, msg: discord.Message = None):
        "Ends a giveaway quickly. If no message id is specified, it will end the most recent giveaway"
        try:
            giveaway = self.find_recent_giveaway(ctx.guild.id, msg)
        except GiveawayNotFound as err:
            await ctx.send(err)
        else:
            await self.finish_giveaway(giveaway)

    @commands.guild_only()
    @commands.bot_has_permissions(read_message_history=True)
    @commands.command()
    async def gdelete(self, ctx: commands.Context, *, msg: discord.Message = None):
        "Deletes a giveaway. If no message id is specified, it will delete the most recent giveaway"
        try:
            giveaway = self.find_recent_giveaway(ctx.guild.id, msg)
        except GiveawayNotFound as err:
            await ctx.send(err)
        else:
            try:
                await (msg or giveaway.message).delete()
            except discord.errors.NotFound:
                pass

            await ctx.send(f"Successfully deleted the giveaway `{giveaway.messageID}`")
            await self.delete_giveaway(giveaway)

    @commands.guild_only()
    @commands.bot_has_permissions(read_message_history=True, embed_links=True)
    @commands.command()
    async def glist(self, ctx: commands.Context):
        "Shows a list of running giveaways in the server"
        lst = [g for g in self.running if g.guild.id == ctx.guild.id]
        if not lst:
            return await ctx.send("❌ There are no running giveaways in this server!")
        
        await ctx.send("\n".join([
            f"**{i+1}]** `{g.messageID}` → {g.channel.mention} | `{g.winners}` **Winner(s)** | **Ends At:** {friendly_duration(g.duration)} | **Title:** `{g.title}`"
            for i, g in enumerate(lst)
        ]))

    @commands.guild_only()
    @commands.bot_has_permissions(read_message_history=True)
    @commands.command()
    async def greroll(self, ctx: commands.Context, *, msg: discord.Message = None):
        "Rerolls the given message id or else rerolls the last giveaway"
        if msg:
            check = next((g for g in self.running if g.messageID == msg.id), None)
            if check:
                return await ctx.send("❌ This giveaway is running right now. Wait for it to end or use the `gend` command to stop it now!")
        else:
            config = await self.bot.db.guilds.find_one({'guild': ctx.guild.id})
            if not config or "lastGiveaway" not in config:
                return await ctx.send("❌ No giveaways were run in this guild!")

            try:
                msg = await ctx.channel.fetch_message(config.get("lastGiveaway"))
            except discord.errors.NotFound:
                return await ctx.send("❌ Could not find that giveaway message in this channel")

        # Verify that its a giveaway message ...
        if msg.author == self.bot.user:
            winners = await select_winners(msg, 1)
            if winners:
                str_winners = ', '.join(w.mention for w in winners)
                await ctx.send(f'🎉 **New winner is:** {str_winners}')
            else:
                await ctx.send("❌ Could not determine a winner")
        else:
            return await ctx.send("❌ Could not find that giveaway message in this channel")


def setup(bot):
    bot.add_cog(GiveawayCog(bot))
