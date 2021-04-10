from enum import IntEnum
from itertools import chain

import discord

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


class Players(IntEnum):
    X = 0
    O = 1
    UNSET = 2


class TicTacToe:
    __slots__ = ('table', 'turn')

    def __init__(self):
        # fmt: off
        self.table = (
            [Players.UNSET, Players.UNSET, Players.UNSET],
            [Players.UNSET, Players.UNSET, Players.UNSET],
            [Players.UNSET, Players.UNSET, Players.UNSET]
        )
        # fmt: on

        self.turn = Players.X

    def _valid_moves_iter(self):
        for column, rows in enumerate(self.table):
            for row, value in enumerate(rows):
                if value == Players.UNSET:
                    yield (3 * column + 1) + row

    def _get_position(self, n):
        return self.table[n // 3][n % 3]

    @property
    def valid_moves(self):
        return tuple(self._valid_moves_iter())

    def make_move(self, n):
        if not (0 <= n < 9):
            raise ValueError('n should be in range(9)')

        if self._get_position(n) != Players.UNSET:
            raise ValueError(f'{n} is already taken.')

        column = n // 3
        row = n % 3

        self.table[column][row] = self.turn
        self.turn = Players(not self.turn)

    def check_winner(self):
        check = self._get_position

        # Check vertical
        for n in range(3):
            if check(n) == check(n + 3) == check(n + 6) != Players.UNSET:
                return check(n)

        # Check horizontal:
        for n in range(3):
            col = 3 * n
            if check(col) == check(col + 1) == check(col + 2) != Players.UNSET:
                return check(col)

        # Check diagonals
        if check(0) == check(4) == check(8) != Players.UNSET:
            return check(0)
        if check(2) == check(4) == check(6) != Players.UNSET:
            return check(2)

        try:
            next(self._valid_moves_iter())
        except StopIteration:
            return Players.UNSET
        else:
            return None


class TicTacToeGame:
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # ID: (message, game, players)
        # X should be at index 0

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

        info = (message, game, (player_x, player_o))
        self.games[player_x.id] = info
        self.games[player_o.id] = info

        await self._update_game(*info)

    async def on_reaction_add(self, reaction, user):
        if not all((user.id in self.games, reaction.emoji in NUMBERS)):
            return

        message, game, players = self.games[user.id]
        player_role = Players(players.index(user))

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
            if v != Players.UNSET:
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
            if winner == Players.UNSET:
                embed.description += _('Deu velha!')
            else:
                embed.description += _('{player} ganhou!', player=players[winner].mention)

        msg = await self._do_rollover(message)

        if msg != message:
            self.bot.loop.create_task(self._add_reactions(msg, game))

            for player in players:
                self.games[player.id] = (msg, game, players)

        await msg.edit(content=None, embed=embed)
