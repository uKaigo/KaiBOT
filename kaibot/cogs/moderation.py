from glob import glob
from functools import cached_property
from os.path import split as split_path

import discord
from discord.ext import commands

from .. import config
from ..i18n import Translator, current_language
from ..utils import can_modify, custom, escape_text, format_list
from ..utils.converters import MemberOrUser, Prefix, Range

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
    async def clear(self, ctx, count: Range[2, 100] = 100, *, member: discord.Member = None):
        """Limpa `count` mensagens do canal."""
        if member:
            check = lambda m: m.author == member and m != ctx.message
        else:
            check = lambda m: m != ctx.message

        async with ctx.typing():
#            await ctx.message.delete()
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
        read_messages = None

        if overwrites := ctx.channel.overwrites.get(role):
            if overwrites.send_messages is False:
                return await ctx.send(_('O canal já está bloqueado.'))

            read_messages = overwrites.read_messages

        await ctx.channel.set_permissions(role, send_messages=False, read_messages=read_messages)

        await ctx.send(_('Canal bloqueado.'))

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Desbloqueia um canal."""
        role = ctx.guild.default_role
        read_messages = None

        if overwrites := ctx.channel.overwrites.get(role):
            if overwrites.send_messages is not False:
                return await ctx.send(_('O canal já está desbloqueado.'))
            read_messages = overwrites.read_messages

        await ctx.channel.set_permissions(role, send_messages=True, read_messages=read_messages)

        await ctx.send(_('Canal desbloqueado.'))

    def _get_no_permission_txt(self, ctx, target):
        if not can_modify(ctx.author, target):
            return _('Você não pode fazer isso com **{member}**.', member=escape_text(target))
        if not can_modify(ctx.me, target):
            return _('Eu não posso fazer isso com **{member}**.', member=escape_text(target))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: MemberOrUser, *, reason=None):
        """
        Bane um membro do servidor.

        O membro não precisa estar no servidor.
        """
        txt = self._get_no_permission_txt(ctx, member)
        if txt:
            return await ctx.send(txt)

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
    async def unban(self, ctx, *, member: discord.User):
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
        txt = self._get_no_permission_txt(ctx, member)
        if txt:
            return await ctx.send(txt)

        if reason is None:
            reason = _('Não especificado.')

        mute_role = discord.utils.get(ctx.guild.roles, name=_('Silenciado'))
        if not mute_role:
            permissions = discord.Permissions(send_messages=False, add_reactions=False, speak=False)
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
                '**{member}** silenciado por **{reason}**.',
                member=escape_text(member),
                reason=escape_text(reason),
            )
        )

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, *, member: discord.Member):
        """Remove o silenciamento de um membro."""
        txt = self._get_no_permission_txt(ctx, member)
        if txt:
            return await ctx.send(txt)

        mute_role = discord.utils.get(ctx.guild.roles, name=_('Silenciado'))
        if not mute_role:
            return await ctx.send(_('Cargo "Silenciado" não encontrado.'))

        await member.remove_roles(mute_role, reason=_('Por {author}', author=ctx.author))

        await ctx.send(_('**{member}** desilenciado.', member=escape_text(member)))

    @cached_property
    def _available_languages(self):
        languages = [l.strip('/') for l in glob('../locales/*/')]
        return [split_path(l)[1] for l in languages] + ['pt_BR']

    def transform_language(self, language):
        def pred(lang):
            full_lang = lang.casefold().replace('-', '_')
            lang_name = full_lang.split('_')[0]
            return language.replace('-', '_').casefold() in [full_lang, lang_name]

        return discord.utils.find(pred, self._available_languages)

    @commands.command(aliases=['setlang'])
    @commands.has_permissions(manage_guild=True)
    async def lang(self, ctx, new_language):
        """Altera a linguagem do servidor."""
        new_language = self.transform_language(new_language)

        available = self._available_languages
        if new_language not in available:
            return await ctx.send(_('Escolha entre {languages}.', languages=format_list(available)))
        if new_language == current_language.get():
            return await ctx.send(_('Essa linguagem já está sendo usada.'))

        to_set = new_language if new_language != config.DEFAULT_LANGUAGE else None

        await self.bot.db.guilds.update(ctx.guild.id, 'set', {'language': to_set})

        current_language.set(new_language)

        await ctx.send(_('Linguagem alterada para {lang}.', lang=new_language))

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """Comandos relacionados ao prefixo do servidor."""
        prefixes = (f'@{self.bot.user.name}',)

        doc = await self.bot.db.guilds.find(ctx.guild.id)
        if not doc or not doc.prefixes:
            prefixes += config.PREFIXES
        else:
            prefixes += tuple(doc.prefixes)

        prefixes = (f'`{prefix}`' for prefix in prefixes)

        await ctx.send(_('Os prefixos do servidor são: {prefixes}', prefixes=format_list(prefixes)))

    @prefix.command(name='add')
    @commands.has_permissions(manage_guild=True)
    async def prefix_add(self, ctx, new_prefix: Prefix):
        """
        Adiciona um prefixo.

        É permitido no máximo 3 prefixos por vez.
        """
        if len(new_prefix) > 5:
            return await ctx.send(_('O prefixo pode ter no máximo 5 caracteres.'))

        doc = await self.bot.db.guilds.find(ctx.guild.id)
        if doc and doc.prefixes:
            if len(doc.prefixes) == 3:
                return await ctx.send(_('O limite de 3 prefixos foi atigindo.'))

            if new_prefix in doc.prefixes:
                return await ctx.send(_('Esse prefixo já está sendo utilizado.'))

        if not doc:
            doc = await self.bot.db.guilds.new(ctx.guild.id)

        doc.prefixes = doc.prefixes or []
        doc.prefixes.append(new_prefix)
        await doc.sync()

        await ctx.send(_('Prefixo `{prefix}` adicionado.', prefix=new_prefix))

    @prefix.command(name='remove', aliases=['rm'])
    @commands.has_permissions(manage_guild=True)
    async def prefix_remove(self, ctx, prefix: Prefix):
        """
        Remove um prefixo.

        Caso todos os prefixos sejam removidos, os padrões serão usados.
        """

        doc = await self.bot.db.guilds.find(ctx.guild.id)
        if not doc or not doc.prefixes or not prefix in doc.prefixes:
            return await ctx.send(_('Este prefixo não está sendo utilizado.'))

        doc.prefixes.remove(prefix)
        await doc.sync()

        await ctx.send(_('Prefixo `{prefix}` removido.', prefix=prefix))


def setup(bot):
    bot.add_cog(Moderation(bot))
