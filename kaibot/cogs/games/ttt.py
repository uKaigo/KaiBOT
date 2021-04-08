import asyncio
from itertools import chain

import discord

from ..resources.ttt_impl import TicTacToe
from ...i18n import Translator, current_language
from ... import config

_ = Translator(__name__)

NUMBERS = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')
TTT_GRID = '''
⁣{}❕{}❕{}
➖➕➖➕➖
{}❕⁣{}❕{}
➖➕➖➕➖
{}❕{}❕{}
'''


class TicTacToeGame:
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # ID: (message, game, players)
        # X should be at index 1

        bot.add_listener(self.on_reaction_add)

    def __contains__(self, value):
        return value in self.games

    def destroy(self):
        self.bot.remove_listener(self.on_reaction_add)
        self.games = {}

    # HELPERS

    async def _add_reactions(self, msg, game):
        for move in game.valid_moves:
            await msg.add_reaction(NUMBERS[move - 1])

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

    # GAME

    async def start(self, message, player_x, player_o):
        game = TicTacToe()

        self.bot.loop.create_task(self._add_reactions(message, game))

        info = (message, game, (player_o, player_x))
        self.games[player_x.id] = info
        self.games[player_o.id] = info

        await self._update_game(*info)

    async def on_reaction_add(self, reaction, user):
        if not all((user.id in self.games, reaction.emoji in NUMBERS)):
            return

        message, game, players = self.games[user.id]
        player_role = players.index(user)

        if not all((message.id == reaction.message.id, game.turn == player_role)):
            return

        move = NUMBERS.index(reaction.emoji)
        try:
            game.make_move(move)
        except ValueError:
            return
        else:
            me = message.guild.me
            if me.permissions_in(message.channel).manage_messages:
                self.bot.loop.create_task(message.clear_reaction(NUMBERS[move]))

        if game.check_winner() != None:
            del self.games[players[0].id], self.games[players[1].id]

        current_language.set(await self.bot.get_language_for(message.guild))
        await self._update_game(message, game, players)

    async def _update_game(self, message, game, players):
        symbols = ('⭕', '❌')
        emojis = []
        for k, v in enumerate(chain(*game.table)):
            if v != -1:
                emojis.append(symbols[v])
            else:
                emojis.append(NUMBERS[k])

        table = TTT_GRID.format(*emojis)

        embed = discord.Embed(
            title=_('Jogo da velha'),
            description=table,
            color=config.MAIN_COLOR,
        )
        embed.description += '\n'

        winner = game.check_winner()
        if winner is None:
            embed.description += _('Vez de {player}.', player=players[game.turn].mention)
        else:
            if winner == -1:
                embed.description += _('Deu velha!')
            else:
                embed.description += _('{player} ganhou!', player=players[winner].mention)

        msg = await self._do_rollover(message)

        if msg != message:
            self.bot.loop.create_task(self._add_reactions(msg, game))

            for player in players:
                self.games[player.id] = (msg, game, players)

        await msg.edit(content=None, embed=embed)
