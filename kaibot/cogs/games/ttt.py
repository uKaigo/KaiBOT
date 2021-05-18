import asyncio
from enum import IntEnum
from itertools import chain
from typing import NamedTuple

import discord

from ... import config
from ...i18n import Translator

_ = Translator(__name__)

# DISPLAY #
NUMBERS = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')
TTT_GRID = '''
⁣{}❕{}❕{}
➖➕➖➕➖
{}❕⁣{}❕{}
➖➕➖➕➖
{}❕{}❕{}
'''

# State Helpers #


class Players(IntEnum):
    X = 0
    O = 1
    UNSET = 2


class GameInfo(NamedTuple):
    message: discord.Message
    game: 'TTTImplementation'
    players: tuple[discord.Member, discord.Member]


# Implementation #
class TTTImplementation:
    __slots__ = ('table', 'turn')

    def __init__(self):
        self.table = (
            [Players.UNSET, Players.UNSET, Players.UNSET],
            [Players.UNSET, Players.UNSET, Players.UNSET],
            [Players.UNSET, Players.UNSET, Players.UNSET],
        )

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

    @property
    def winner(self):
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


# Integration #
class TTTIntegration:
    def __init__(self, bot):
        self.bot = bot
        self.games: dict[int, GameInfo] = {}
        self.__tasks = []

    def __contains__(self, value):
        return value in self.games

    def destroy(self):
        for task in self.tasks:
            task.cancel()
        self.games = {}

    # HELPERS

    def _create_task(self, coro):
        task = self.bot.loop.create_task(coro)
        self.__tasks.append(task)
        task.add_done_callback(lambda f: self.__tasks.remove(task))

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

    def _get_check(self, message, game, players):
        def predicate(reaction, user):
            checks = (
                user.id in self.games,
                reaction.emoji in NUMBERS,
                message.id == reaction.message.id,
            )
            return all(checks) and game.turn == Players(players.index(user))

        return predicate

    # GAME

    async def start(self, message, player_x, player_o):
        game = TTTImplementation()

        self._create_task(self._add_reactions(message, game))

        info = GameInfo(message, game, (player_x, player_o))
        self.games[player_x.id] = info
        self.games[player_o.id] = info

        self._create_task(self._internal_loop(*info))
        await self._update_game(*info)

    async def _internal_loop(self, _, game, players):
        try:
            bot = self.bot
            while game.winner is None:
                # We need to dinamically access message, so rollover
                # works.
                message = self.games[players[0].id][0]

                check = self._get_check(message, game, players)
                reaction, _ = await bot.wait_for('reaction_add', check=check, timeout=60 * 3)

                move = NUMBERS.index(reaction.emoji)
                try:
                    game.make_move(move)
                except ValueError:
                    continue
                else:
                    if message.guild.me.permissions_in(message.channel).manage_messages:
                        self._create_task(message.clear_reaction(NUMBERS[move]))

                await self._update_game(message, game, players)
        except asyncio.TimeoutError:
            return
        finally:
            del self.games[players[0].id], self.games[players[1].id]

    async def _update_game(self, message, game, players):
        symbols = ('❌', '⭕')
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

        winner = game.winner
        if winner is None:
            embed.description += _('Vez de {player}.', player=players[game.turn].mention)
        else:
            if winner == Players.UNSET:
                embed.description += _('Deu velha!')
            else:
                embed.description += _('{player} ganhou!', player=players[winner].mention)

        msg = await self._do_rollover(message)

        if msg != message and game.winner is None:
            self._create_task(self._add_reactions(msg, game))

            for player in players:
                self.games[player.id] = (msg, game, players)

        await msg.edit(content=None, embed=embed)
