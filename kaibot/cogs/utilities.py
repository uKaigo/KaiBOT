from secrets import randbelow
import discord

from discord.ext import commands

from .. import config
from ..utils import custom
from ..i18n import Translator

_ = Translator(__name__)


class Utilities(custom.Cog, translator=_):
    """Comandos úteis."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, sides: int):
        """
        Rola um dado de `SIDES` lados.

        O dado precisa ter pelo menos 2 lados.
        """
        if sides < 2:
            return await ctx.send(_('Insira um dado de pelo menos 2 lados.'))

        result = randbelow(sides + 1) or 1
        return await ctx.send(_('Seu dado resultou em: {result}', result=result))

    @commands.command()
    async def resolve(self, ctx, link):
        """Mostra todos os redirecionamentos do link."""
        embed = discord.Embed(title=_('Redirecionamentos'), color=config.MAIN_COLOR)

        description = ''
        async with ctx.typing():
            dest = await self.bot.session.get(link.strip('<>'))

            for index, res in enumerate(dest.history + (dest,)):
                em = '🔷' if index in (0, len(dest.history)) else '🔹'
                description += f'{em} `{res.status}` - {res.url}\n'

        embed.description = description

        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utilities(bot))
