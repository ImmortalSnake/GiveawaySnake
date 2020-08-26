import inspect

from discord.ext import commands


class Context(commands.Context):
    async def get_config(self):
        if not ctx.guild:
            return {}

        return await self.bot.db.guilds.find_one({"guild": ctx.guild.id})

    async def prompt(self, question, *, converter=str, timeout=60):
        def check(m):
            return m.author == self.author and m.channel == self.channel
        
        await self.send(question)
        while True:
            res = await self.bot.wait_for('message', timeout=timeout, check=check)
            # Must handle timeout errors
            try:
                if inspect.isclass(converter) and issubclass(converter, commands.Converter):
                    return await converter().convert(self, res.content)
                return converter(res.content)
            except commands.BadArgument as err:
                await self.send(err)

    async def ask(self, question, *, timeout=60):
        msg = await self.send(question)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')

        def check(reaction, user):
            return user == self.author and reaction.message.id == msg.id and str(reaction.emoji) in ['✅', '❌']
        

        reaction, user = await self.bot.wait_for('reaction_add', timeout=timeout, check=check)
        # Must handle timeout errors
        return str(reaction.emoji) == '✅'
