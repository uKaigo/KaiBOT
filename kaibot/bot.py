import logging

import discord
from discord.ext import commands

from . import config
from .utils import get_intents

log = logging.getLogger('kaibot')

intents = discord.Intents(**{intent: True for intent in config.INTENTS})


class KaiBOT(commands.Bot):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('intents', intents)
        kwargs.setdefault('command_prefix', self.prefix_getter)

        fmt_intents = ', '.join(get_intents(kwargs['intents']))
        log.debug(f'Running with the following intents: {fmt_intents}')

        super().__init__(*args, **kwargs)

    def load_all_extensions(self, extensions):
        for extension in extensions:
            try:
                self.load_extension(extension, package=__package__)
            except:
                log.exception(f'[{extension}] Not loaded.')
            else:
                log.info(f'[{extension}] Loaded.')

    def prefix_getter(self, _, message):
        return config.PREFIX
