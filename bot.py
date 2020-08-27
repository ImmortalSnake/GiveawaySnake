from datetime import datetime
import logging

import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from config import TOKEN, MONGO_URI
from cogs.utils.context import Context


COGS = [
    'cogs.admin',
    'cogs.config',
    'cogs.errors',
    'cogs.general',
    'cogs.giveaway'
]


async def prefix_resolver(bot, msg):
    prefixes = [f'<@{bot.user.id}> ', f'<@!{bot.user.id}> ']
    prefix = 'm!'
    if msg.guild:
        config = bot.guild_config.get(msg.guild.id)
        if config:
            prefix = config.get('prefix', 'm!')
    
    prefixes.append(prefix)
    return prefixes


class GiveawaySnake(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=prefix_resolver, case_insensitive=True, reconnect=True, owner_id=410806297580011520)

        self.version = 'v0.0.1'
        self.invite = ''
        self.guild_config = {}
    
    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=Context)

    async def on_connect(self):
        print(f"\n{self.user} is starting up...")

        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client.dpy

        async for conf in self.db.guilds.find({}, {'id': 0}):
            guildid = conf.pop('guild')
            self.guild_config[guildid] = conf

        print("Successfully connected to mongodb server")

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=1, name=f"development"))
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.utcnow()

        for cog in COGS:
            try:
                self.load_extension(cog)
            except Exception as err:
                print(f"\nFailed to load extension: {cog}")
                print(err)

        print("\n==========================================")
        print(f"Successfully connected to {self.user}")
        print(f"Ready to serve {len(self.guilds)} Guilds")
        print("==========================================\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    GiveawaySnake().run(TOKEN)
