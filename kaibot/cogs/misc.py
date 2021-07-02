from datetime import datetime
import sys

import psutil
import discord
import humanize
from discord.ext import commands


from .. import config
from ..i18n import Translator, current_language
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
        txt = _('🏓 Pong\n- Websocket: {}ms\n- Database: {}ms\n- Tempo de resposta: {}ms')
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
            icon_url=ctx.me.avatar,
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

    @commands.command(aliases=['bi'])
    async def botinfo(self, ctx):
        """Informações sobre mim."""
        embed = discord.Embed(color=config.MAIN_COLOR)
        embed.set_author(name=_('Informações sobre mim'), icon_url=self.bot.user.avatar)

        who_am_i = _('Sou KaiBOT, um bot criado para te ajudar no seu servidor.')
        who_am_i += '\n' + _(
            'Tenho vários comandos, incluindo moderação, diversão, utilitários e mais!'
        )

        embed.add_field(name=_('Quem sou eu?'), value=who_am_i, inline=False)

        delta = datetime.utcnow() - self.bot.uptime
        if current_language.get() != 'en_US':
            humanize.activate(current_language.get())
        else:
            humanize.deactivate()

        embed.add_field(
            name=_('Estou online a:'),
            value=humanize.precisedelta(delta, format='%d') + '.',
            inline=False,
        )

        stats = _('{commands} comandos.', commands=len(self.bot.commands))
        stats += '\n' + _('{guilds} servidores.', guilds=len(self.bot.guilds))

        embed.add_field(name=_('Possuo:'), value=stats, inline=False)

        resources = ''
        proc = psutil.Process()

        with proc.oneshot():
            mem = proc.memory_full_info()
            resources += _('Usando {mem} de memória RAM.', mem=humanize.naturalsize(mem.uss))

            # TRANSLATORS: There's a "%" after percent, it was removed
            # Babel doesn't insert the python-format flag.
            resources += '\n' + _('Usando {percent} de CPU.', percent=f'{proc.cpu_percent()}%')

        embed.add_field(name=_('Recursos:'), value=resources, inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Miscelaneous(bot))


def teardown(bot):
    # Uncache the help command to allow reloading.
    sys.modules.pop('kaibot.cogs.resources.help')
