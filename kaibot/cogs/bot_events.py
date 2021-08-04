from datetime import datetime
from io import StringIO
from kaibot.utils import escape_text
from sys import version_info as py_version_i

import discord
from discord import version_info as dpy_version_i
from discord.ext import commands
from rich import box, get_console
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from .. import config

ASCII_ART = r'''
 _   __      _______  _____ _____ 
| | / /     (_) ___ \|  _  |_   _|
| |/ /  __ _ _| |_/ /| | | | | |  
|    \ / _` | | ___ \| | | | | |  
| |\  \ (_| | | |_/ /\ \_/ / | |  
\_| \_/\__,_|_\____/  \___/  \_/  
'''.strip(
    '\n'
)

color = f'#{hex(config.MAIN_COLOR)[2:]}'


class BotEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _set_info_from_server(self, ctx, embed):
        if ctx.guild.chunked:
            owner = f'\> Dono: {ctx.guild.owner} ({ctx.guild.owner.id})'
        else:
            owner = f'\> Dono: {ctx.guild.owner_id} (id)'

        embed.add_field(
            name='Servidor',
            value=f'\> Nome: {ctx.guild.name}\n\> ID: {ctx.guild.id}\n' + owner,
            inline=False,
        )

        if isinstance(ctx.channel, discord.Thread):
            embed.add_field(
                name='Canal',
                value=(
                    f'\> Nome: {ctx.channel.parent.name}\n'
                    f'\> ID: {ctx.channel.parent.id}\n'
                    f'\> NSFW: {ctx.channel.parent.nsfw}'
                ),
                inline=False,
            )

            embed.add_field(
                name='Thread',
                value=(f'\> Nome: {ctx.channel.name}\n \> ID: {ctx.channel.id}\n'),
                inline=False,
            )
        else:
            embed.add_field(
                name='Canal',
                value=(
                    f'\> Nome: {ctx.channel.name}\n'
                    f'\> ID: {ctx.channel.id}\n'
                    f'\> NSFW: {ctx.channel.nsfw}'
                ),
                inline=False,
            )

    def _set_info_from_dm(self, ctx, embed):
        embed.add_field(name='Servidor', value='_Executado em DM._', inline=False)
        embed.add_field(name='Canal', value=f'\> ID: {ctx.channel.id}', inline=False)

    @commands.Cog.listener()
    async def on_ready(self):
        bot = self.bot
        if bot.uptime is not None:
            return
        bot.uptime = datetime.utcnow()

        console = get_console()
        console.print(f'[{color}]{ASCII_ART}\n')

        stats = Table(show_edge=False, show_header=False, box=box.MINIMAL)

        stats.add_row('Guilds', str(len(self.bot.guilds)))

        stats.add_row('Members', str(sum(g.member_count for g in bot.guilds)))

        versions = Table(show_edge=False, show_header=False, box=box.MINIMAL)
        fmt = '{0.major}.{0.minor}.{0.micro}'
        versions.add_row('Python', fmt.format(py_version_i))
        versions.add_row('discord.py', fmt.format(dpy_version_i))

        console.print(
            Columns(
                (
                    Panel(stats, title='Stats', expand=False),
                    Panel(versions, title='Version', expand=False),
                ),
                equal=True,
            ),
            style=color,
        )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        channel = self.bot.get_channel(config.LOGS['commands'])

        embed = discord.Embed(
            title=f'Comando "{ctx.command.qualified_name}" executado.',
            color=config.MAIN_COLOR,
        )

        embed.set_author(
            name=f'{ctx.author} [{ctx.author.id}]',
            icon_url=ctx.author.avatar,
        )

        if ctx.guild:
            self._set_info_from_server(ctx, embed)
        else:
            self._set_info_from_dm(ctx, embed)

        content = discord.utils.escape_markdown(ctx.message.clean_content)
        croped_content = content[:850] + ('...' if len(content) > 850 else '')
        embed.add_field(
            name='Mensagem',
            value=(
                f'\> Conteúdo: "{croped_content}"\n'
                f'\> ID: {ctx.message.id}\n'
                f'\> URL: [Link]({ctx.message.jump_url})'
            ),
            inline=False,
        )

        file = None
        if len(content) > 850:
            stream = StringIO(content[851:])
            file = discord.File(stream, 'message_content.txt')

        embed.timestamp = ctx.message.created_at
        await channel.send(embed=embed, file=file)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel = self.bot.get_channel(config.LOGS['guilds'])

        embed = discord.Embed(title='Novo servidor', color=config.MAIN_COLOR)
        embed.set_author(name=f'{guild.name} [{guild.id}]', icon_url=guild.icon)
        embed.description = f'Dono: <@{guild.owner_id}>'

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel = self.bot.get_channel(config.LOGS['guilds'])

        embed = discord.Embed(title='Removido de um servidor', color=config.MAIN_COLOR)
        embed.set_author(name=f'{guild.name} [{guild.id}]', icon_url=guild.icon)
        embed.description = f'Dono: <@{guild.owner_id}>'

        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(BotEvents(bot))
