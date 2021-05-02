import discord
from discord.ext import commands

from ..i18n import Translator
from ..utils import can_modify, custom, escape_text
from ..utils.converters import MemberOrUser, Range

_ = Translator(__name__)


class Moderation(custom.Cog, translator=_):
    """Comandos de moderação."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

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
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: MemberOrUser, *, reason=None):
        """
        Bane um membro do servidor.

        O membro não precisa estar no servidor.
        """
        if not can_modify(ctx.author, member):
            return await ctx.send(
                _('Você não tem permissão para banir **{member}**.', member=escape_text(member)),
            )
        if not can_modify(ctx.me, member):
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
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.User):
        """Desbane um membro do servidor."""
        try:
            await ctx.guild.unban(member, reason=_('Por {author}', author=ctx.author))
        except discord.NotFound:
            return await ctx.send(_('O membro não está banido.'))

        await ctx.send(_('**{member}** desbanido.', member=escape_text(member)))

    async def _update_overwrites(self, guild, role):
        overwrite = discord.PermissionOverwrite(
            send_messages=False, add_reactions=False, speak=False
        )
        reason = _('Criando o cargo de Silenciado')
        for channel in guild.channels:
            await channel.set_permissions(role, overwrite=overwrite, reason=reason)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        """Silencia um membro."""
        if not can_modify(ctx.author, member):
            msg = _(
                'Você não tem permissão para silenciar **{member}**.',
                member=escape_text(member),
            )
            return await ctx.send(msg)
        if not can_modify(ctx.me, member):
            return await ctx.send(
                _('Eu não tenho permissão para silenciar **{member}**.', member=escape_text(member))
            )

        if reason is None:
            reason = _('Não especificado.')

        mute_role = discord.utils.get(ctx.guild.roles, name=_('Silenciado'))
        if not mute_role:
            permissions = discord.Permissions.text()
            permissions.update(send_messages=False, add_reactions=False, speak=False)
            mute_role = await ctx.guild.create_role(
                name=_('Silenciado'),
                permissions=permissions,
                color=0x6D6D6D,
                reason=_('Criando o cargo de Silenciado'),
            )

            self.bot.loop.create_task(self._update_overwrites(ctx.guild, mute_role))

        await member.add_roles(
            mute_role, reason=_('Por {author} | Motivo: {reason}', author=ctx.author, reason=reason)
        )

        await ctx.send(
            _(
                '**{member}** silenciado por **{reason}**',
                member=escape_text(member),
                reason=escape_text(reason),
            )
        )

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Remove o silenciamento de um membro."""
        if not can_modify(ctx.author, member):
            msg = _(
                'Você não tem permissão para desilenciar **{member}**.',
                member=escape_text(member),
            )
            return await ctx.send(msg)
        if not can_modify(ctx.me, member):
            msg = _(
                'Eu não tenho permissão para desilenciar **{member}**.',
                member=escape_text(member),
            )
            return await ctx.send(msg)

        mute_role = discord.utils.get(ctx.guild.roles, name=_('Silenciado'))
        if not mute_role:
            return await ctx.send(_('Cargo "Silenciado" não encontrado.'))

        await member.remove_roles(mute_role, reason=_('Por {author}', author=ctx.author))

        await ctx.send(_('**{member}** desilenciado.', member=escape_text(member)))


def setup(bot):
    bot.add_cog(Moderation(bot))
