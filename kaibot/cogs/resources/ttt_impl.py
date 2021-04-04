class TicTacToe:
    __slots__ = ('table', 'turn')

    # fmt: off
    def __init__(self):
        # -1 = Nothing
        # 0 = Circle
        # 1 = X
        self.table = (
            [-1, -1, -1],
            [-1, -1, -1],
            [-1, -1, -1]
        )
        self.turn = 1

    def _valid_moves_iter(self):
        for column, rows in enumerate(self.table):
            for row, value in enumerate(rows):
                if value == -1:
                    yield (3 * column + 1) + row

    def _get_position(self, n):
        return self.table[n // 3][n % 3]

    @property
    def valid_moves(self):
        return tuple(self._valid_moves_iter())

    def make_move(self, n):
        if not (0 <= n < 9):
            raise ValueError('n should be in range(9)')

        if self._get_position(n) != -1:
            raise ValueError(f'{n} is already taken.')

        column = n // 3
        row = n % 3

        self.table[column][row] = self.turn
        self.turn = int(not self.turn)

    def check_winner(self):
        check = self._get_position

        # Check vertical
        for n in range(3):
            if check(n) == check(n + 3) == check(n + 6) != -1:
                return check(n)

        # Check horizontal:
        for n in range(3):
            col = 3 * n
            if check(col) == check(col + 1) == check(col + 2) != -1:
                return check(col)

        # Check diagonals
        if check(0) == check(4) == check(8) != -1:
            return check(0)
        if check(2) == check(4) == check(6) != -1:
            return check(2)

        try:
            next(self._valid_moves_iter())
        except StopIteration:
            return -1
        else:
            return None
