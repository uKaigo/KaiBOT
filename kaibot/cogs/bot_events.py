from sys import version_info as py_version_i
from datetime import datetime

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


def setup(bot):
    bot.add_cog(BotEvents(bot))
