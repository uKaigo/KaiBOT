from typing import Union

import discord
from discord.ext import commands

from .translations import ERRORS

MemberOrUser = Union[discord.Member, discord.User]


class BadArgument(commands.BadArgument):
    """Local BadArgument to distinguish between library BadArgument."""

    is_kaibot = True


class Range(commands.Converter):
    def __init__(self, min_, max_):
        self.min = min_
        self.max = max_

    async def convert(self, ctx, argument):
        try:
            num = int(argument)
        except ValueError:
            raise commands.BadArgument('Failed to convert to int.')

        if not self.max >= num > self.min:
            raise BadArgument(str(ERRORS['not_in_range']).format(self))
        return num

    def __class_getitem__(cls, slc):
        if isinstance(slc, tuple):
            min_ = slc[0]
            max_ = slc[1]
        else:
            min_ = 0
            max_ = slc
        return cls(min_, max_)
