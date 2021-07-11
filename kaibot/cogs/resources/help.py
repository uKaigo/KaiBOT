import discord
from discord.ext import commands, menus

from ... import config
from ...i18n import Translator
from ...utils import format_list
from ...utils.enums import Emotes

_ = Translator(__name__)


def _get_short_doc(command):
    # We can't translate command.short_doc
    if not command.help:
        return _('Sem descrição.')

    cmd_help = getattr(command, 'translator', Translator._noop)(command.help)
    return cmd_help.split('\n', 1)[0]


class HelpView(discord.ui.View):
    def __init__(self, source, message):
        self.source = source
        self.current_page = 0
        self.message = message
        super().__init__(timeout=60)

    async def show_current_page(self):
        entry = await self.source.get_page(self.current_page)
        embed = self.source.format_page(self, entry)

        for child in self.children:
            if child.emoji in {Emotes.FIRST, Emotes.PREVIOUS}:
                child.disabled = self.current_page == 0
            elif child.emoji in {Emotes.LAST, Emotes.NEXT}:
                child.disabled = self.current_page == self.source.get_max_pages() - 1
            else:
                child.disabled = False

        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(emoji=Emotes.FIRST, style=discord.ButtonStyle.blurple)
    async def go_to_first(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = 0
        await self.show_current_page()

    @discord.ui.button(emoji=Emotes.PREVIOUS, style=discord.ButtonStyle.blurple)
    async def go_to_previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page -= 1
        await self.show_current_page()

    @discord.ui.button(emoji=Emotes.STOP, style=discord.ButtonStyle.red)
    async def stop_help(self, button: discord.ui.Button, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

    @discord.ui.button(emoji=Emotes.NEXT, style=discord.ButtonStyle.blurple)
    async def go_to_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page += 1
        await self.show_current_page()

    @discord.ui.button(emoji=Emotes.LAST, style=discord.ButtonStyle.blurple)
    async def go_to_last(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = self.source.get_max_pages() - 1
        await self.show_current_page()

    @discord.ui.button(emoji=Emotes.QUESTION, row=1)
    async def show_help(self, button: discord.ui.Button, interaction: discord.Interaction):
        # TODO: Use a different view to go back to the menu.
        embed = discord.Embed(color=config.MAIN_COLOR)
        embed.description = _('A estrutura é simples.')
        embed.set_author(name=_('Ajuda'), icon_url=self.message.guild.me.avatar)

        fields = (
            ('<argument>', _('Isto significa que o argumento é __**obrigatório**__.')),
            ('[argument]', _('Isto significa que o argumento é __**opcional**__.')),
            ('[argument=X]', _('Isto significa que o valor padrão do argumento é __**X**__. ')),
        )

        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)

        button.disabled = True

        await self.message.edit(embed=embed, view=self)


# TODO: Don't use BotSource
class BotSource(menus.GroupByPageSource):
    def __init__(self, *args, **kwargs):
        self.help = kwargs.pop('help')
        super().__init__(*args, **kwargs)

    def format_page(self, menu, entry):
        key, cmds = entry
        ctx = self.help.context
        cog = ctx.bot.get_cog(key)

        embed = discord.Embed(color=config.MAIN_COLOR)
        embed.set_author(name=_('Comandos de {name}', name=key), icon_url=ctx.me.avatar)
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

    @property
    def clean_prefix(self):
        # TODO: Remove this alias.
        if self.context:
            return self.context.clean_prefix

    def _fake_command_not_found(self):
        return self.send_error_message(self.command_not_found(self.context.kwargs['command']))

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
        msg = await self.get_destination().send('\N{ZERO WIDTH SPACE}')

        view = HelpView(source, msg)
        await view.show_current_page()

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
            icon_url=self.bot.user.avatar,
        )

        self._insert_command_info(embed, command)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        translator = getattr(group, 'translator', Translator._noop)

        embed = discord.Embed(description=translator(group.help), color=config.MAIN_COLOR)
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=group.name), icon_url=self.bot.user.avatar
        )

        self._insert_command_info(embed, group)

        paginator = commands.Paginator('', '', 1024)

        for command in group.commands:
            signature = f'{self.clean_prefix}{self.get_command_signature(command)}'

            doc = _get_short_doc(command).strip()
            if isinstance(command, commands.Group):
                doc += '\n' + _('_Possui subcomandos._')

            paginator.add_line(f'**{signature}**\n{doc}\n')

        embed.add_field(name=_('Subcomandos:'), value=paginator.pages[0], inline=False)
        for page in paginator.pages[1:]:
            embed.add_field(name='\N{ZERO WIDTH SPACE}', value=page, inline=False)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        translator = getattr(cog, '__translator__', Translator._noop)

        embed = discord.Embed(description=translator(cog.description), color=config.MAIN_COLOR)
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=cog.qualified_name, icon_url=self.bot.user.avatar)
        )

        cmds = await self.filter_commands(cog.get_commands())
        if not cmds:
            return await self._fake_command_not_found()

        for command in cmds:
            signature = f'{self.clean_prefix}{self.get_command_signature(command)}'

            doc = _get_short_doc(command).strip()
            if isinstance(command, commands.Group):
                doc += '\n' + _('_Possui subcomandos._')

            embed.add_field(name=signature, value=doc, inline=False)

        await self.get_destination().send(embed=embed)
