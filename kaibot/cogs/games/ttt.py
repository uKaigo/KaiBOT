from enum import IntEnum

import discord
import discord.http

from ...utils.enums import Emotes
from ...i18n import Translator

_ = Translator(__name__)

# State Helpers #


class Players(IntEnum):
    X = 0
    O = 1
    UNSET = 2


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


class TTTButton(discord.ui.Button):
    def __init__(self, n):
        label = '\u200b' + ' ' * 7 + '\u200b'
        super().__init__(label=label, row=(n // 3), style=discord.ButtonStyle.gray)
        self.n = n

    async def callback(self, interaction: discord.Interaction):
        board = self.view.board

        try:
            board.make_move(self.n)
        except ValueError:
            return

        self.style = discord.ButtonStyle.blurple
        self.label = None

        if board.turn == Players.O:
            self.emoji = Emotes.X
        else:
            self.emoji = Emotes.O

        await self.view.date_message(self.view, interaction.response)


class TTTView(discord.ui.View):
    def __init__(self, message, players):
        super().__init__(timeout=60)
        self.board = TTTImplementation()
        self.message = message
        self.players = players

        for column in range(3):
            for row in range(3):
                self.add_item(TTTButton((3 * column) + row))

    async def update_message(self, response: discord.InteractionResponse):
        winner = self.board.winner

        players = self.players

        message = self.message
        channel = message.channel

        if winner is None:
            txt = _('Vez de {player}.', player=players[self.board.turn].mention)
        else:
            if winner == Players.UNSET:
                txt = _('Deu velha!')
            else:
                txt = _('{player} ganhou!', player=players[winner].mention)

            for child in self.children:
                child.disabled = True

            self.stop()

        if channel.last_message != message:
            history = await channel.history(limit=6, after=message).flatten()
            if len(history) > 5:
                await response.defer()

                try:
                    await message.delete()
                except discord.HTTPException:
                    pass

                self.message = await channel.send(content=txt, view=self)
                return

        await response.edit_message(content=txt, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content=_('Tempo excedido.'), view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user not in self.players:
            await interaction.response.send_message(_('Você não está nesse jogo.'), ephemeral=True)
            return False

        if self.players.index(interaction.user) != self.board.turn:
            await interaction.response.send_message(_('Não é a sua vez.'), ephemeral=True)
            return False

        return True
