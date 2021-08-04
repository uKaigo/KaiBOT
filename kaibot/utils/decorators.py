import asyncio
import functools

import discord
from discord.ext import commands

from .translations import ERRORS


class NoThread(commands.CheckFailure):
    is_kaibot = True


async def needs_chunk_hook(self, ctx):
    if ctx.guild and not ctx.guild.chunked and ctx.bot.intents.members:
        async with ctx.typing():
            await ctx.guild.chunk()


def needs_chunk():
    """Registers a before_invoke that'll chunk the guild."""

    def decorator(func):
        if isinstance(func, commands.Command):
            func.before_invoke(needs_chunk_hook)
        else:
            func.__before_invoke__ = needs_chunk_hook
        return func

    return decorator


def in_executor(func):
    """Makes a blocking function non-blocking."""
    loop = asyncio.get_event_loop()

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        partial = functools.partial(func, *args, **kwargs)
        return loop.run_in_executor(None, partial)

    return decorator


def no_thread():
    async def predicate(ctx):
        if isinstance(ctx.channel, discord.Thread):
            raise NoThread(str(ERRORS['no_thread']))
        return True

    return commands.check(predicate)
