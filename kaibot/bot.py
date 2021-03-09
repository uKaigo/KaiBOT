import logging

from discord.ext import commands

from . import config
from .utils import get_selected_intents, get_intents_from

log = logging.getLogger('kaibot')


class KaiBOT(commands.Bot):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('intents', get_intents_from(config.INTENTS))
        kwargs['command_prefix'] = self.prefix_getter

        fmt_intents = ', '.join(get_selected_intents(kwargs['intents']))
        log.debug(f'Running with the following intents: {fmt_intents}')

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
                log.error(f'Failed to load {extension}.', exc_info=exc_info)
            else:
                log.info(f'Loaded "{extension}".')

        log.debug(f'Loaded {len(self.extensions)} extensions with {len(self.commands)} commands.')

    def prefix_getter(self, *_):
        return config.PREFIX

    async def on_ready(self):
        log.info('Bot is ready.')
