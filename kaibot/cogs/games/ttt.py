import asyncio
from enum import IntEnum
from typing import NamedTuple

import discord
import discord.http

from ...i18n import Translator
from ...utils.interactions import ack_interaction, wait_for_click

_ = Translator(__name__)

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
CUSTOM_ID_PREFIX = 'btn_'


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

    async def edit_message(self, msg, txt, game, force_disabled=False):
        route = discord.http.Route(
            'PATCH',
            '/channels/{channel_id}/messages/{message_id}',
            channel_id=msg.channel.id,
            message_id=msg.id,
        )

        payload = {'content': txt, 'allowed_mentions': {'parse': ['users']}}
        payload['components'] = []

        disabled = game.winner is not None or force_disabled

        for column, rows in enumerate(game.table):
            btn_row = []
            for row, value in enumerate(rows):
                base = {
                    'type': 2,
                    'custom_id': CUSTOM_ID_PREFIX + str((3 * column + 1) + row),
                    'disabled': disabled,
                }
                if value == Players.UNSET:
                    base['style'] = 2
                    base['label'] = '\u200b' + ' ' * 7 + '\u200b'
                elif value == Players.X:
                    base['style'] = 1
                    base['emoji'] = {'id': '863602074285375520'}
                elif value == Players.O:
                    base['style'] = 1
                    base['emoji'] = {'id': '863602074545553418'}
                btn_row.append(base)
            payload['components'].append({'type': 1, 'components': btn_row})

        await self.bot.http.request(route, json=payload)

    # GAME

    async def start(self, message, player_x, player_o):
        game = TTTImplementation()

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

                player = players[game.turn]
                move = await wait_for_click(self.bot, message.id, player.id, timeout=120)

                try:
                    game.make_move(int(move[len(CUSTOM_ID_PREFIX) :]) - 1)
                except ValueError:
                    continue

                await self._update_game(message, game, players)
        except asyncio.TimeoutError:
            message = self.games[players[0].id][0]
            return await self.edit_message(message, 'Tempo excedido', game, True)
        finally:
            del self.games[players[0].id], self.games[players[1].id]

    async def _update_game(self, message, game, players):
        winner = game.winner
        if winner is None:
            txt = _('Vez de {player}.', player=players[game.turn].mention)
        else:
            if winner == Players.UNSET:
                txt = _('Deu velha!')
            else:
                txt = _('{player} ganhou!', player=players[winner].mention)

        msg = await self._do_rollover(message)

        if msg != message and game.winner is None:
            for player in players:
                self.games[player.id] = (msg, game, players)

        await self.edit_message(msg, txt, game)
