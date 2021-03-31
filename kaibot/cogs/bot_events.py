from sys import version_info as py_version_i
from datetime import datetime

import discord
from discord import version_info as dpy_version_i
from discord.ext import commands
from rich import get_console, box
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

from .. import config


ASCII_ART = r"""
 _   __      _______  _____ _____ 
| | / /     (_) ___ \|  _  |_   _|
| |/ /  __ _ _| |_/ /| | | | | |  
|    \ / _` | | ___ \| | | | | |  
| |\  \ (_| | | |_/ /\ \_/ / | |  
\_| \_/\__,_|_\____/  \___/  \_/  
""".strip('\n')

color = f'#{hex(config.MAIN_COLOR)[2:]}'


class BotEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        channels = len(tuple(bot.get_all_channels()))
        stats.add_row('Channels', str(channels))

        versions = Table(show_edge=False, show_header=False, box=box.MINIMAL)
        fmt = '{0.major}.{0.minor}.{0.minor}'
        versions.add_row('Python', fmt.format(py_version_i))
        versions.add_row('discord.py', fmt.format(dpy_version_i))

        console.print(
            Columns((
                Panel(
                    stats,
                    title='Stats',
                    expand=False
                ),
                Panel(
                    versions,
                    title='Version',
                    expand=False
                )
            ), equal=True),
            style=color
        )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        channel = self.bot.get_channel(config.LOGS['commands'])

        embed = discord.Embed(
            title=f'Comando "{ctx.command.qualified_name}" executado.',
            color=self.bot.color
        )

        embed.set_author(name=f'{ctx.author} ({ctx.author.id})', icon_url=ctx.author.avatar_url)

        embed.add_field(name='Servidor', inline=False, value=(
            f'\> Nome: {ctx.guild.name}\n'
            f'\> ID: {ctx.guild.id}\n'
            f'\> Dono: {ctx.guild.owner} ({ctx.guild.owner.id})'
        ))

        embed.add_field(name='Canal', inline=False, value=(
            f'\> Nome: {ctx.channel.name}\n'
            f'\> ID: {ctx.channel.id}\n'
            f'\> NSFW: {ctx.channel.nsfw}'
        ))

        embed.add_field(name='Mensagem', inline=False, value=(
            f'\> Conteúdo: "{ctx.message.clean_content}"\n'
            f'\> ID: {ctx.message.id}\n'
            f'\> URL: [Link]({ctx.message.jump_url})'
        ))

        embed.timestamp = ctx.message.created_at
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(BotEvents(bot))
