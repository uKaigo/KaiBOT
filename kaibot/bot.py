import logging
import aiohttp

from discord import Activity, ActivityType, DMChannel
from discord.ext import commands

from . import config
from .i18n import current_language
from .utils import get_intents_from

log = logging.getLogger('kaibot')


class KaiBOT(commands.Bot):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('intents', get_intents_from(config.INTENTS))
        kwargs['command_prefix'] = self.prefix_getter
        kwargs['activity'] = Activity(name='k.help', type=ActivityType.listening)

        super().__init__(*args, **kwargs)

        self.uptime = None
        self.session = aiohttp.ClientSession()
        self.load_all_extensions(config.EXTENSIONS)

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
        return config.DEFAULT_LANGUAGE

    def prefix_getter(self, bot, message):
        if isinstance(message.channel, DMChannel):
            return commands.when_mentioned_or(*config.PREFIXES, '')(bot, message)
        return commands.when_mentioned_or(*config.PREFIXES)(bot, message)

    async def on_ready(self):
        log.info('Bot is ready.')

    async def on_message(self, message):
        current_language.set(await self.get_language_for(message.guild))
        await self.process_commands(message)

    async def close(self):
        await self.session.close()
        await super().close()
