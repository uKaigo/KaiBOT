import io
from collections import defaultdict
from concurrent.futures import CancelledError


class BrainfuckDecoder:
    def __init__(self, input_):
        self.input = io.StringIO(input_ + '\x00')
        self.mem = defaultdict(int)
        self.ptr = 0
        self.cancelled = False

    def _raise_if_cancelled(self):
        if self.cancelled:
            raise CancelledError()

    def _parse(self, code, output):
        while_code = None
        enclosure_count = 0

        for char in code:
            self._raise_if_cancelled()
            if char == ']' and while_code is not None and enclosure_count == 0:
                code = while_code
                while_code = None
                while self.mem[self.ptr]:
                    self._parse(code, output)

            elif while_code is not None:
                if char == '[':
                    enclosure_count += 1
                elif char == ']':
                    enclosure_count -= 1
                while_code += char
            elif char == '>':
                self.ptr += 1
            elif char == '<':
                self.ptr -= 1
            elif char == '+':
                self.mem[self.ptr] += 1
            elif char == '-':
                self.mem[self.ptr] -= 1
            elif char == '.':
                try:
                    output.write(chr(self.mem[self.ptr]))
                except ValueError:
                    # Not in range
                    output.write('\N{REPLACEMENT CHARACTER}')
            elif char == ',':
                _tmp = ord(self.input.read(1))
                if _tmp == 0:
                    self.input.seek(0)
                else:
                    self.mem[self.ptr] = _tmp if _tmp else -1
            elif char == '[':
                while_code = ''

    def __call__(self, code):
        output = io.StringIO()

        try:
            self._parse(code, output)
        except CancelledError:
            return

        return output.getvalue()
