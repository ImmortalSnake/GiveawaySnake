import inspect

from discord.ext import commands


class PromptCancelled(Exception):
    pass


class Context(commands.Context):
    def get_config(self):
        # Default Config
        config = {'prefix': 'm!', 'giveawayrole': None}
        if not self.guild:
            return config

        config.update(self.bot.guild_config.get(self.guild.id, {}))
        return config

    async def update_config(self, data):
        await self.bot.db.guilds.update_one(
            {"guild": self.guild.id},
            {"$set": data},
            upsert=True
        )
        config = self.bot.guild_config.get(self.guild.id, {})
        config.update(data)
        self.bot.guild_config[self.guild.id] = config

    async def prompt(self, question, *, converter=str, timeout=60):
        def check(msg):
            return msg.author == self.author and msg.channel == self.channel

        await self.send(question)
        while True:
            res = await self.bot.wait_for('message', timeout=timeout, check=check)
            if res.content.lower() == 'cancel':
                raise PromptCancelled()
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

        reaction, _ = await self.bot.wait_for('reaction_add', timeout=timeout, check=check)
        # Must handle timeout errors
        return str(reaction.emoji) == '✅'
