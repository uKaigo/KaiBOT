import logging

import discord
from discord.ext import commands

from . import config
from .utils import get_selected_intents, get_intents_for

log = logging.getLogger('kaibot')


class KaiBOT(commands.Bot):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('intents', get_intents_for(config.INTENTS))
        kwargs.setdefault('command_prefix', self.prefix_getter)

        fmt_intents = ', '.join(get_selected_intents(kwargs['intents']))
        log.debug(f'Running with the following intents: {fmt_intents}')

        super().__init__(*args, **kwargs)

    def load_all_extensions(self, extensions):
        for extension in extensions:
            try:
                self.load_extension(extension, package=__package__)
            except:
                log.exception(f'Failed to load {extension}.')
            else:
                log.info(f'Loaded "{extension}".')

    def prefix_getter(self, _, message):
        return config.PREFIX
