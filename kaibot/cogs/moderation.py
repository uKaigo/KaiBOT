import discord
from discord.ext import commands

from ..i18n import Translator
from ..utils import can_ban, custom, escape_text
from ..utils.converters import MemberOrUser, Range

_ = Translator(__name__)


class Moderation(custom.Cog, translator=_):
    """Comandos de moderação."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx, count: Range[2, 100] = 100, member: discord.Member = None):
        """Limpa `count` mensagens do canal."""
        if member:
            check = lambda m: m.author == member and m != ctx.message
        else:
            check = lambda m: m != ctx.message

        async with ctx.typing():
            await ctx.message.delete()
            deleted = await ctx.channel.purge(limit=count, check=check)

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

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: MemberOrUser, *, reason=None):
        """
        Bane um membro do servidor.

        O membro não precisa estar no servidor.
        """
        if not can_ban(ctx.author, member):
            return await ctx.send(
                _('Você não tem permissão para banir **{member}**.', member=escape_text(member)),
            )
        if not can_ban(ctx.me, member):
            return await ctx.send(
                _('Eu não tenho permissão para banir **{member}**.', member=escape_text(member))
            )

        if reason is None:
            reason = _('Não especificado.')

        audit_reason = _('Por {author} | Motivo: {reason}', author=ctx.author, reason=reason)

        await ctx.guild.ban(member, reason=audit_reason)

        await ctx.send(
            _(
                '**{member}** banido por **{reason}**.',
                member=escape_text(member),
                reason=escape_text(reason),
            )
        )

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.User):
        """Desbane um membro do servidor."""
        try:
            await ctx.guild.unban(member, reason=_('Por {member}', member=ctx.author))
        except discord.NotFound:
            return await ctx.send(_('O membro não está banido.'))

        await ctx.send(_('**{member}** desbanido.', member=escape_text(member)))


def setup(bot):
    bot.add_cog(Moderation(bot))
