from enum import IntEnum

import discord


class Emotes:
    X = discord.PartialEmoji(name='X_', id=863602074285375520)
    O = discord.PartialEmoji(name='O_', id=863602074545553418)
    FIRST = discord.PartialEmoji(name='first', id=863600652881494036)
    PREVIOUS = discord.PartialEmoji(name='previous', id=863600653841727539)
    STOP = discord.PartialEmoji(name='stop', id=863600655189278730)
    NEXT = discord.PartialEmoji(name='next', id=863600653636993055)
    LAST = discord.PartialEmoji(name='last', id=863600653972144178)
    QUESTION = discord.PartialEmoji(name='question_', id=863600654740094977)


class Flags(IntEnum):
    VIP = 1
    TRANSLATOR = 2
    DEVELOPER = 4
