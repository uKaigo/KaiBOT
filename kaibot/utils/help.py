import discord
from discord.ext import commands

from .. import config
from ..i18n import Translator

_ = Translator(__name__)


class Help(commands.HelpCommand):
    def _get_short_doc(self, command):
        # We can't translate command.short_doc
        if not command.help:
            return _('Sem descrição.')
        translate = Translator(command.cog.__module__)

        cmd_help = translate(command.help)
        return cmd_help.split('\n', 1)[0]

    def command_not_found(self, string):
        return _('Comando "{string}" não foi encontrado.', string=string)

    def subcommand_not_found(self, command, string):
        if isinstance(command, commands.Group) and command.commands:
            return _(
                'O comando "{command}" não possui um subcomando chamado "{string}"',
                command=command.qualified_name,
                string=string
            )
        return _('O comando "{command}" não possui subcomandos.', command=command.qualified_name)

    async def send_error_message(self, error):
        embed = discord.Embed(description=error, color=config.MAIN_COLOR)
        await self.get_destination().send(embed=embed)

    def get_command_signature(self, command):
        return f'{command.qualified_name} {command.signature}'

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

    async def send_command_help(self, command):
        translator = Translator(command.cog.__module__)

        embed = discord.Embed(
            description=translator(command.help),
            color=config.MAIN_COLOR
        )
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=command.name.title()),
            icon_url=self.context.me.avatar_url
        )
        embed.add_field(
            name=_('Modo de usar:'),
            value=f'{self.clean_prefix}{self.get_command_signature(command)}',
            inline=False
        )
        if command.aliases:
            embed.add_field(name=_('Sinônimos:'), value=', '.join(command.aliases), inline=False)

        if command.parent:
            embed.add_field(name=_('Parente:'), value=command.parent.qualified_name)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        translator = Translator(group.cog.__module__)

        embed = discord.Embed(
            description=translator(group.help),
            color=config.MAIN_COLOR
        )
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=group.name.title()),
            icon_url=self.context.me.avatar_url
        )
        embed.add_field(
            name=_('Modo de usar:'),
            value=f'{self.clean_prefix}{self.get_command_signature(group)}',
            inline=False
        )
        if group.aliases:
            embed.add_field(name=_('Sinônimos:'), value=', '.join(group.aliases), inline=False)

        if group.parent:
            embed.add_field(name=_('Parente:'), value=group.parent.qualified_name, inline=False)

        if group.commands:
            commands = await self.filter_commands(group.commands, sort=True)
            if commands:
                txt = ''
                for command in commands:
                    cmd_doc = self._get_short_doc(command)
                    txt += f'**{command.name} {command.signature}** — {cmd_doc}\n'

                embed.add_field(name=_('Subcomandos:'), value=txt)

            embed.add_field(name='\N{ZERO WIDTH SPACE}', inline=False, value=_(
                'Use "{prefix}{group} [subcomando]" para mais informações sobre um comando.',
                prefix=self.clean_prefix,
                group=group.qualified_name
            ))

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        translator = Translator(cog.__module__)

        embed = discord.Embed(color=config.MAIN_COLOR, description=translator(cog.description))
        embed.set_author(
            name=_('Ajuda | {bucket}', bucket=cog.qualified_name),
            icon_url=self.context.me.avatar_url
        )

        commands = await self.filter_commands(cog.get_commands(), sort=True)
        if not commands:
            return await self.send_error_message(self.command_not_found(cog.qualified_name))

        txt = ''
        for command in commands:
            cmd_text = self.get_command_signature(command)
            txt += f'**{cmd_text}** — {self._get_short_doc(command)}\n'

        embed.description += f'\n\n{txt}'
        embed.description += '\n' + _(
            'Use "{prefix}help [comando]" para mais informações sobre um comando.',
            prefix=self.clean_prefix
        )
        await self.get_destination().send(embed=embed)
