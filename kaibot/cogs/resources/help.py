import discord
from discord.ext import commands

from ... import config
from ...i18n import Translator

_ = Translator(__name__)


class Help(commands.HelpCommand):
    def _get_short_doc(self, command):
        # We can't translate command.short_doc
        if not command.help:
            return _('Sem descrição.')

        cmd_help = command.translator(command.help)
        return cmd_help.split('\n', 1)[0]

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
        embed = discord.Embed(
            description=_('Aqui estão todos os meus comandos.'),
            color=config.MAIN_COLOR,
        )
        embed.set_author(name=_('Ajuda'), icon_url=self.context.me.avatar_url)

        for cog, cmds in mapping.items():
            cmds = await self.filter_commands(cmds, sort=True)
            if not cmds:
                continue

            txt = ''
            for command in cmds:
                cmd_text = self.get_command_signature(command)
                if isinstance(command, commands.Group) and command.commands:
                    txt += '\*'
                txt += f'**{cmd_text}** — {self._get_short_doc(command)}\n'

            embed.add_field(name=cog.qualified_name, value=txt, inline=False)

        extra = _(
            'Use "{prefix}help [comando]" para mais informações sobre um comando, ou '
            '"{prefix}help [categoria]" para mais informações sobre uma categoria.',
            prefix=self.clean_prefix,
        )
        extra += '\n\n' + _(
            'Comandos começando com `*` são grupos, portanto possuem subcomandos.'
        )
        embed.add_field(name='\N{ZERO WIDTH SPACE}', value=extra, inline=False)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        translator = command.translator

        embed = discord.Embed(
            description=translator(command.help), color=config.MAIN_COLOR
        )
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=command.name.title()),
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
                value=', '.join(command.aliases),
                inline=False,
            )

        if command.parent:
            embed.add_field(
                name=_('Parente:'), value=command.parent.qualified_name
            )

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        translator = group.translator

        embed = discord.Embed(
            description=translator(group.help), color=config.MAIN_COLOR
        )
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=group.name.title()),
            icon_url=self.context.me.avatar_url,
        )
        embed.add_field(
            name=_('Modo de usar:'),
            value=f'{self.clean_prefix}{self.get_command_signature(group)}',
            inline=False,
        )
        if group.aliases:
            embed.add_field(
                name=_('Sinônimos:'),
                value=', '.join(group.aliases),
                inline=False,
            )

        if group.parent:
            embed.add_field(
                name=_('Parente:'),
                value=group.parent.qualified_name,
                inline=False,
            )

        if group.commands:
            cmds = await self.filter_commands(group.commands, sort=True)
            if cmds:
                txt = ''
                for command in cmds:
                    cmd_doc = self._get_short_doc(command)
                    if (
                        isinstance(command, commands.Group)
                        and command.commands
                    ):
                        txt += '\*'

                    txt += (
                        f'**{command.name} {command.signature}** — {cmd_doc}\n'
                    )

                embed.add_field(name=_('Subcomandos:'), value=txt)

            extra = _(
                'Use "{prefix}help {group} [subcomando]" para mais informações sobre um comando.',
                prefix=self.clean_prefix,
                group=group.qualified_name,
            )
            extra += '\n\n' + _(
                'Comandos começando com `*` são grupos, portanto possuem subcomandos.'
            )
            embed.add_field(
                name='\N{ZERO WIDTH SPACE}', value=extra, inline=False
            )

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        translator = cog.__translator__

        embed = discord.Embed(
            color=config.MAIN_COLOR, description=translator(cog.description)
        )
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=cog.qualified_name),
            icon_url=self.context.me.avatar_url,
        )

        cmds = await self.filter_commands(cog.get_commands(), sort=True)
        if not cmds:
            return await self.send_error_message(
                self.command_not_found(cog.qualified_name)
            )

        txt = ''
        for command in cmds:
            cmd_text = self.get_command_signature(command)

            if isinstance(command, commands.Group) and command.commands:
                txt = '\*'

            txt += f'**{cmd_text}** — {self._get_short_doc(command)}\n'

        embed.description += f'\n\n{txt}'
        embed.description += '\n' + _(
            'Use "{prefix}help [comando]" para mais informações sobre um comando.',
            prefix=self.clean_prefix,
        )
        embed.description += '\n\n' + _(
            'Comandos começando com `*` são grupos, portanto possuem subcomandos.'
        )
        await self.get_destination().send(embed=embed)
