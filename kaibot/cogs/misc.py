import sys

import discord
from discord.ext import commands

from .. import config
from ..i18n import Translator
from ..utils import custom
from .resources.help import Help

_ = Translator(__name__)


class Miscelaneous(custom.Cog, translator=_):
    """Comandos que não se encaixam em outra categoria."""

    def __init__(self, bot):
        self.bot = bot
        bot._old_help_command = bot.help_command
        bot.help_command = Help(
            verify_checks=False,
            command_attrs={
                'aliases': ['ajuda'],
                'help': _('Mostra essa mensagem.'),
                'max_concurrency': commands.MaxConcurrency(
                    1, per=commands.BucketType.member, wait=False
                ),
            },
        )
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.bot._old_help_command

    @commands.command()
    async def ping(self, ctx):
        """Envia a latência da websocket e o tempo de resposta."""
        txt = _('🏓 Ping\n- Websocket: {}ms\n- Database: {}ms\n- Tempo de resposta: {}ms')
        msg = await ctx.send(txt.format('NaN', 'NaN', 'NaN'))

        diff = (msg.created_at - ctx.message.created_at).total_seconds()
        db_ping = await self.bot.db.guilds.ping()

        await msg.edit(
            content=txt.format(int(self.bot.latency * 1000), int(db_ping * 1000), int(diff * 1000))
        )

    @commands.command(aliases=['privacidade'])
    async def privacy(self, ctx):
        """Políticas de privacidade."""
        embed = discord.Embed(color=config.MAIN_COLOR, description='')
        embed.set_author(
            name=_('Políticas de privacidade | KaiBOT'),
            icon_url=ctx.me.avatar_url,
        )

        embed.description += _(
            'As políticas de privacidade podem ser encontradas [nesse link]({policy}).',
            policy='https://gist.github.com/uKaigo/ac2c76098eae2c2abc5e82bb19b80cb9',
        )
        embed.description += '\n' + _(
            'Caso você não concorda com essa política, pare de usar o bot e (opcionalmente) '
            'peça a exclusão dos seus dados.'
        )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Miscelaneous(bot))


def teardown(bot):
    # Uncache the help command to allow reloading.
    sys.modules.pop('kaibot.cogs.resources.help')
