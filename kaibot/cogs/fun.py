import sys

import discord
from discord.ext import commands

from ..i18n import Translator
from ..utils import custom, escape_text
from .games.ttt import TTTIntegration

_ = Translator(__name__)


class Fun(custom.Cog, translator=_):
    """Comandos de diversão."""

    def __init__(self, bot):
        self.bot = bot
        self._ttt_game = TTTIntegration(bot)

    def cog_unload(self):
        self._ttt_game.destroy()

    @commands.command(aliases=['tictactoe', 'jogodavelha', 'jdv'])
    @commands.guild_only()
    async def ttt(self, ctx, player: discord.Member):
        """Começa um jogo da velha."""
        if player.bot:
            return await ctx.send(_('O outro jogador não pode ser um bot.'))
        if ctx.author == player:
            return await ctx.send(_('Você não pode jogar com você mesmo.'))
        if ctx.author.id in self._ttt_game:
            return await ctx.send(_('Você já está em um jogo.'))
        if player.id in self._ttt_game:
            return await ctx.send(
                _('**{player}** já está em um jogo.', player=escape_text(player.display_name))
            )

        msg = await ctx.send('\N{ZERO WIDTH SPACE}')

        await self._ttt_game.start(msg, ctx.author, player)


def setup(bot):
    bot.add_cog(Fun(bot))


def teardown(bot):
    sys.modules.pop('kaibot.cogs.games.ttt')
