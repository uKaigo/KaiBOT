from typing import Optional

import discord
from discord.ext import commands

from ..i18n import Translator
from ..utils import custom
from ..utils.converters import Range

_ = Translator(__name__)


class Moderation(custom.Cog, name=_('Moderação'), translator=_):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx, member: Optional[discord.Member], count: Range[2, 100] = 100):
        """
        Limpa `count` mensagens do canal.

        Um membro pode ser definido pelo primeiro argumento.
        """
        if member:
            check = lambda m: m.author == member and m != ctx.message
        else:
            check = lambda m: m != ctx.message

        async with ctx.typing():
            deleted = await ctx.channel.purge(limit=count + 1, check=check)

        txt = _('{count} mensagens foram deletadas.', count=len(deleted))
        await ctx.send(txt, delete_after=3)
        await ctx.message.delete(delay=3)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Bloqueia um canal."""
        role = ctx.guild.default_role
        overwrites = ctx.channel.overwrites.get(role)
        read_messages = None
        if overwrites:
            if overwrites.send_messages is False:
                return await ctx.send(_('O canal já está bloqueado.'))
            read_messages = overwrites.read_messages

        await ctx.channel.set_permissions(
            role,
            send_messages=False,
            # There is a bug where read_messages is reset.
            read_messages=read_messages,
        )

        await ctx.send(_('Canal bloqueado.'))

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Desbloqueia um canal."""
        role = ctx.guild.default_role
        overwrites = ctx.channel.overwrites.get(role)
        read_messages = None
        if overwrites:
            if overwrites.send_messages is not False:
                return await ctx.send(_('O canal já está desbloqueado.'))
            read_messages = overwrites.read_messages

        await ctx.channel.set_permissions(
            role,
            send_messages=True,
            # There is a bug where read_messages is reset.
            read_messages=read_messages,
        )

        await ctx.send(_('Canal desbloqueado.'))


def setup(bot):
    bot.add_cog(Moderation(bot))
