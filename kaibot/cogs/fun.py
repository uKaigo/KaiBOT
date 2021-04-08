from itertools import chain

import discord
from discord.ext import commands

from .. import config
from ..i18n import Translator, current_language
from ..utils import custom
from .resources.ttt_impl import TicTacToe

_ = Translator(__name__)

NUMBERS = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')
TTT_GRID = '''
⁣{}❕{}❕{}
➖➕➖➕➖
{}❕⁣{}❕{}
➖➕➖➕➖
{}❕{}❕{}
'''


class Fun(custom.Cog, translator=_):
    """Comandos de diversão."""

    def __init__(self, bot):
        self.bot = bot
        self._ttt_games = {}  # ID: (message, game, players)
        # X should be at index 1

    async def _do_rollover(self, message):
        channel = message.channel
        if channel.last_message == message:
            return message

        history = await channel.history(limit=6, after=message).flatten()
        if len(history) > 5:
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            return await channel.send('\N{ZERO WIDTH SPACE}')
        return message

    # ---- TIC TAC TOE ---- #

    async def _update_ttt_game(self, message, game, players):
        symbols = ('⭕', '❌')
        emojis = []
        for k, v in enumerate(chain(*game.table)):
            if v != -1:
                emojis.append(symbols[v])
            else:
                emojis.append(NUMBERS[k])

        table = TTT_GRID.format(*emojis)
        winner = game.check_winner()
        embed = discord.Embed(
            title=_('Jogo da velha'),
            description=table,
            color=config.MAIN_COLOR,
        )
        embed.description += '\n'
        if winner is None:
            embed.description += _(
                'Vez de {player}.', player=players[game.turn].mention
            )
        else:
            if winner == -1:
                embed.description += _('Deu velha!')
            else:
                embed.description += _(
                    '{player} ganhou!', player=players[winner].mention
                )

        msg = await self._do_rollover(message)

        if msg != message:

            async def add_reactions():
                for move in game.valid_moves:
                    await msg.add_reaction(NUMBERS[move - 1])

            self.bot.loop.create_task(add_reactions())

            for player in players:
                self._ttt_games[player.id] = (msg, game, players)

        await msg.edit(content=None, embed=embed)

    @commands.command(aliases=['tictactoe', 'jogodavelha', 'jdv'])
    async def ttt(self, ctx, player: discord.Member):
        """Começa um jogo da velha."""
        if player.bot:
            return await ctx.send(_('O outro jogador não pode ser um bot.'))
        if ctx.author == player:
            return await ctx.send(_('Você não pode jogar com você mesmo.'))
        if ctx.author.id in self._ttt_games:
            return await ctx.send(_('Você já está em um jogo.'))
        if player.id in self._ttt_games:
            return await ctx.send(
                _('{player} já está em um jogo.', player=player.display_name)
            )

        async def add_reactions(msg):
            for reaction in NUMBERS:
                await msg.add_reaction(reaction)

        msg = await ctx.send('\N{ZERO WIDTH SPACE}')

        self.bot.loop.create_task(add_reactions(msg))

        game = TicTacToe()
        info = (msg, game, (player, ctx.author))
        self._ttt_games[ctx.author.id] = info
        self._ttt_games[player.id] = info

        await self._update_ttt_game(*info)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not all((user.id in self._ttt_games, reaction.emoji in NUMBERS)):
            return

        message, game, players = self._ttt_games[user.id]
        player_role = players.index(user)

        if not all(
            (message.id == reaction.message.id, game.turn == player_role)
        ):
            return

        move = NUMBERS.index(reaction.emoji)
        try:
            game.make_move(move)
        except ValueError:
            return
        else:
            me = message.guild.me
            if me.permissions_in(message.channel).manage_messages:
                self.bot.loop.create_task(
                    message.clear_reaction(NUMBERS[move])
                )

        if game.check_winner() != None:
            del self._ttt_games[players[0].id], self._ttt_games[players[1].id]

        current_language.set(await self.bot.get_language_for(message.guild))
        await self._update_ttt_game(message, game, players)

    # --------------------- #


def setup(bot):
    bot.add_cog(Fun(bot))
