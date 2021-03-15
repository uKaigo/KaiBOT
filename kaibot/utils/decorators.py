from functools import partial

from discord.ext import commands


async def needs_chunk_hook(self, ctx):
    if ctx.guild and not ctx.guild.chunked and ctx.bot.intents.members:
        async with ctx.typing():
            await ctx.guild.chunk()


def needs_chunk():
    def decorator(func):
        if isinstance(func, commands.Command):
            func.before_invoke(needs_chunk_hook)
        else:
            func.__before_invoke__ = needs_chunk_hook
        return func
    return decorator
