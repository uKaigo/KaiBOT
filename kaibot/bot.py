import logging
import os

import aiohttp
from discord import Activity, ActivityType, DMChannel, AllowedMentions
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from . import config
from .i18n import current_language
from .utils import get_intents_from
from .utils.database import DatabaseManager

log = logging.getLogger('kaibot')


class KaiBOT(commands.Bot):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('intents', get_intents_from(config.INTENTS))
        kwargs['command_prefix'] = self.prefix_getter
        kwargs['activity'] = Activity(name='k.help', type=ActivityType.listening)
        kwargs['allowed_mentions'] = AllowedMentions(everyone=False, users=False, roles=False)

        super().__init__(*args, **kwargs)

        self.uptime = None
        self.session = aiohttp.ClientSession()

        self.db_client = AsyncIOMotorClient(os.environ['MONGO_URI'])
        self.db = DatabaseManager('KaiBOT', client=self.db_client)
        self.db.create_collection('Guilds', {'prefix': None, 'language': None})

        self.load_all_extensions(config.EXTENSIONS)

    # - HELPERS -

    async def close(self):
        await self.session.close()
        await super().close()

    def load_all_extensions(self, extensions):
        for extension in extensions:
            try:
                self.load_extension(extension, package=__package__)
            except Exception as e:
                e = e.__cause__ or e
                exc_info = (type(e), e, e.__traceback__)
                log.error(f'Failed to load "{extension}".', exc_info=exc_info)
            else:
                log.info(f'Loaded "{extension}".')

        log.debug(f'Loaded {len(self.extensions)} extensions with {len(self.commands)} commands.')

    async def get_language_for(self, guild):
        doc = await self.db.guilds.find(guild.id)
        if doc and doc.language:
            return doc.language

        return config.DEFAULT_LANGUAGE

    async def prefix_getter(self, bot, message):
        if isinstance(message.channel, DMChannel):
            return commands.when_mentioned_or(*config.PREFIXES, '')(bot, message)

        prefixes = config.PREFIXES

        doc = await self.db.guilds.find(message.guild.id)
        if doc and doc.prefix:
            prefixes = [doc.prefix]

        return commands.when_mentioned_or(*prefixes)(bot, message)

    # - EVENTS -

    async def on_ready(self):
        log.info('Bot is ready.')

    async def on_message(self, message):
        current_language.set(await self.get_language_for(message.guild))
        await self.process_commands(message)
