import discord
from discord.ext import commands, menus

from ... import config
from ...i18n import Translator
from ...utils import format_list

_ = Translator(__name__)


def _get_short_doc(command):
    # We can't translate command.short_doc
    if not command.help:
        return _('Sem descrição.')

    cmd_help = command.translator(command.help)
    return cmd_help.split('\n', 1)[0]


class HelpMenuPages(menus.MenuPages):
    @menus.button('❔', position=menus.Last(3))
    async def show_help(self, payload):
        embed = discord.Embed(color=config.MAIN_COLOR)
        embed.description = _('Este help está organizado de maneira simples.')
        embed.set_author(name=_('Ajuda'), icon_url=self.ctx.me.avatar_url)

        fields = (
            ('<argument>', _('Isto significa que o argumento é __**obrigatório**__.')),
            ('[argument]', _('Isto significa que o argumento é __**opcional**__.')),
        )

        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)

        await self.message.edit(embed=embed)


class BotSource(menus.GroupByPageSource):
    def __init__(self, *args, **kwargs):
        self.help = kwargs.pop('help')
        super().__init__(*args, **kwargs)

    def format_page(self, menu, entry):
        key, cmds = entry
        ctx = self.help.context
        cog = ctx.bot.get_cog(key)
        cog_name = cog.__translator__(cog.qualified_name)

        embed = discord.Embed(color=config.MAIN_COLOR)
        embed.set_author(name=_('Comandos de {name}', name=cog_name), icon_url=ctx.me.avatar_url)
        embed.description = cog.__translator__(cog.description)

        for command in cmds:
            signature = f'{self.help.clean_prefix}{self.help.get_command_signature(command)}'

            doc = _get_short_doc(command).strip()
            if isinstance(command, commands.Group) and command.commands:
                doc += '\n' + _('_Possui subcomandos._')

            embed.add_field(name=signature, value=doc, inline=False)

        current_page = menu.current_page + 1
        embed.set_footer(
            text=_('Página {current}/{max}', current=current_page, max=self.get_max_pages())
        )

        return embed


class Help(commands.HelpCommand):
    @property
    def cog(self):
        return self._command_impl.cog

    @cog.setter
    def cog(self, cog):
        self._command_impl._eject_cog()

        # If a new cog is set then inject it.
        if cog is not None:
            self._command_impl._inject_into_cog(cog)
            # Set the translator
            self._command_impl.translator = cog.__translator__

    @property
    def bot(self):
        if self.context:
            return self.context.bot

    def command_not_found(self, string):
        return _('Comando "{string}" não foi encontrado.', string=string)

    def subcommand_not_found(self, command, string):
        if isinstance(command, commands.Group) and command.commands:
            return _(
                'O comando "{command}" não possui um subcomando chamado "{string}"',
                command=command.qualified_name,
                string=string,
            )
        return _(
            'O comando "{command}" não possui subcomandos.',
            command=command.qualified_name,
        )

    async def send_error_message(self, error):
        embed = discord.Embed(description=error, color=config.MAIN_COLOR)
        await self.get_destination().send(embed=embed)

    def get_command_signature(self, command):
        return f'{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        commands = await self.filter_commands(self.bot.commands)
        key = lambda cmd: cmd.cog.qualified_name
        source = BotSource(entries=commands, per_page=10, key=key, help=self)
        pages = HelpMenuPages(source=source, check_embeds=True, clear_reactions_after=True)

        await pages.start(self.context)

    async def send_command_help(self, command):
        translator = command.translator

        embed = discord.Embed(description=translator(command.help), color=config.MAIN_COLOR)
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=command.name),
            icon_url=self.context.me.avatar_url,
        )
        embed.add_field(
            name=_('Modo de usar:'),
            value=f'{self.clean_prefix}{self.get_command_signature(command)}',
            inline=False,
        )
        if command.aliases:
            embed.add_field(
                name=_('Sinônimos:'),
                value=format_list(command.aliases),
                inline=False,
            )

        if command.parent:
            embed.add_field(name=_('Parente:'), value=command.parent.qualified_name)

        await self.get_destination().send(embed=embed)
