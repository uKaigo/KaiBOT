import sys

from discord.ext import commands

from .utils.help import Help
from ..i18n import Translator

_ = Translator(__name__)


class Miscelaneous(commands.Cog):
    """Comandos que não se encaixam em outra categoria."""

    def __init__(self, bot):
        self.bot = bot
        bot._old_help_command = bot.help_command
        bot.help_command = Help(
            verify_checks=False,
            command_attrs={
                'aliases': ['ajuda'],
                'help': _('Mostra essa mensagem.')
            }
        )
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.bot._old_help_command

    @commands.command()
    async def ping(self, ctx):
        """Envia a latência da websocket e o tempo de resposta."""
        txt = _(
            '🏓 Ping\n'
            '- Websocket: {}ms\n'
            '- Tempo de resposta: {}ms'
        )
        msg = await ctx.send(txt.format('NaN', 'NaN'))
        diff = (msg.created_at - ctx.message.created_at).total_seconds()

        await msg.edit(content=txt.format(int(self.bot.latency * 1000), int(diff * 1000)))


def setup(bot):
    bot.add_cog(Miscelaneous(bot))


def teardown():
    # Uncache the help command to allow reloading.
    sys.modules.pop('kaibot.cogs.utils.help', None)
