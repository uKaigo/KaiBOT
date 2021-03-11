import logging
import os

from discord import Activity, ActivityType
from discord.ext import commands

from . import config
from .utils import get_intents_from

log = logging.getLogger('kaibot')

os.environ.update({f'JISHAKU_{FLAG}': '1' for FLAG in config.JISHAKU_FLAGS})


class KaiBOT(commands.Bot):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('intents', get_intents_from(config.INTENTS))
        kwargs['command_prefix'] = self.prefix_getter
        kwargs['activity'] = Activity(name='k.help', type=ActivityType.listening)

        super().__init__(*args, **kwargs)

        self.uptime = None
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

    def prefix_getter(self, *_):
        return config.PREFIX

    async def on_ready(self):
        log.info('Bot is ready.')
