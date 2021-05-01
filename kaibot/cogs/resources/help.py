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

    cmd_help = getattr(command, 'translator', Translator._noop)(command.help)
    return cmd_help.split('\n', 1)[0]


class HelpMenuPages(menus.MenuPages):
    @menus.button('❔', position=menus.Last(3))
    async def show_help(self, payload):
        embed = discord.Embed(color=config.MAIN_COLOR)
        embed.description = _('A estrutura é simples.')
        embed.set_author(name=_('Ajuda'), icon_url=self.ctx.me.avatar_url)

        fields = (
            ('<argument>', _('Isto significa que o argumento é __**obrigatório**__.')),
            ('[argument]', _('Isto significa que o argumento é __**opcional**__.')),
            ('[argument=X]', _('Isto significa que o valor padrão do argumento é __**X**__. ')),
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

        embed = discord.Embed(color=config.MAIN_COLOR)
        embed.set_author(name=_('Comandos de {name}', name=key), icon_url=ctx.me.avatar_url)
        embed.description = getattr(cog, '__translator__', Translator._noop)(cog.description)

        for command in cmds:
            signature = f'{self.help.clean_prefix}{self.help.get_command_signature(command)}'

            doc = _get_short_doc(command).strip()
            if isinstance(command, commands.Group):
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

        await pages.start(self.context, channel=self.get_destination())

    def _insert_command_info(self, embed, command):
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

    async def send_command_help(self, command):
        translator = getattr(command, 'translator', Translator._noop)

        embed = discord.Embed(description=translator(command.help), color=config.MAIN_COLOR)
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=command.name),
            icon_url=self.bot.user.avatar_url,
        )

        self._insert_command_info(embed, command)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        translator = getattr(group, 'translator', Translator._noop)

        embed = discord.Embed(description=translator(group.help), color=config.MAIN_COLOR)
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=group.name), icon_url=self.bot.user.avatar_url
        )

        self._insert_command_info(embed, group)

        subcommands = ''

        for command in group.commands:
            signature = f'{self.clean_prefix}{self.get_command_signature(command)}'

            doc = _get_short_doc(command).strip()
            if isinstance(command, commands.Group):
                doc += '\n' + _('_Possui subcomandos._')

            subcommands += f'**{signature}**\n{doc}\n\n'

        embed.add_field(name=_('Subcomandos:'), value=subcommands, inline=False)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        translator = getattr(cog, '__translator__', Translator._noop)

        embed = discord.Embed(description=translator(cog.description), color=config.MAIN_COLOR)
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=cog.qualified_name, icon_url=self.bot.user.avatar_url)
        )

        cmds = await self.filter_commands(cog.get_commands())
        for command in cmds:
            signature = f'{self.clean_prefix}{self.get_command_signature(command)}'

            doc = _get_short_doc(command).strip()
            if isinstance(command, commands.Group):
                doc += '\n' + _('_Possui subcomandos._')

            embed.add_field(name=signature, value=doc, inline=False)

        await self.get_destination().send(embed=embed)
