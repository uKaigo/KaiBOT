import asyncio
import functools

from discord.ext import commands


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


def in_executor(loop=None):
    """Makes a blocking function non-blocking."""
    loop = loop or asyncio.get_event_loop()

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            partial = functools.partial(func, *args, **kwargs)
            return loop.run_in_executor(None, partial)

        return wrapper

    return decorator
