from datetime import datetime
import logging

import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from config import TOKEN, MONGO_URI


COGS = [
    'cogs.general',
    'cogs.admin',
    'cogs.giveaway',
    'cogs.errors'
]


def prefix_resolver(bot, msg):
    prefixes = [f'<@{bot.user.id}> ', f'<@!{bot.user.id}> ']
    prefixes.append('m!')
    return prefixes


class GiveawaySnake(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=prefix_resolver, reconnect=True, owner_id=410806297580011520)

        self.version = 'v0.0.1'
        self.invite = ''

    async def on_connect(self):
        print(f"\n{self.user} is starting up...")

        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client.dpy

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


logging.basicConfig(level=logging.INFO)
ModerationBot().run(TOKEN)
