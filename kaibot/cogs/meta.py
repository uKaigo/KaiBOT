import discord
from discord.ext import commands

from .. import config
from ..i18n import Translator

_ = Translator(__name__)


class Help(commands.MinimalHelpCommand):
    def _get_short_doc(self, command):
        # We can't translate command.short_doc
        if not command.help:
            return _('Sem descrição.')
        translator = Translator(command.cog.__module__)

        cmd_help = translator(command.help)
        return cmd_help.split('\n', 1)[0]

    def get_command_signature(self, command):
        return f'{command.name} {command.signature}'

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            description=_('Aqui estão todos os meus comandos.'),
            color=config.MAIN_COLOR
        )
        embed.set_author(name=_('Ajuda'), icon_url=self.context.me.avatar_url)

        for cog, commands in mapping.items():
            commands = await self.filter_commands(commands, sort=True)
            if not commands:
                continue

            txt = ''
            for command in commands:
                cmd_text = self.get_command_signature(command)
                txt += f'**{cmd_text}** — {self._get_short_doc(command)}\n'

            embed.add_field(name=cog.qualified_name, value=txt, inline=False)

        embed.add_field(
            name='\N{ZERO WIDTH SPACE}',
            value=_(
                'Use "{prefix}help [comando]" para mais informações sobre um comando, ou '
                '"{prefix}help [categoria]" para mais informações sobre uma categoria.',
                prefix=self.clean_prefix
            ),
            inline=False
        )

        await self.get_destination().send(embed=embed)


class Meta(commands.Cog):
    """Comandos diversos."""

    def __init__(self, bot):
        self.bot = bot
        bot.help_command = Help(
            verify_checks=False,
            command_attrs={
                'help': _('Mostra essa mensagem.')
            }
        )
        bot.help_command.cog = self

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
    bot.add_cog(Meta(bot))
