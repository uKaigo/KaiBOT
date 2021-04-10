from random import choice

import discord
from discord.ext import commands, menus

from .. import config
from ..utils import format_datetime, format_list, custom
from ..utils.decorators import needs_chunk
from ..utils.converters import MemberOrUser
from ..utils.translations import PERMISSIONS
from ..i18n import Translator

_ = Translator(__name__)


class UserinfoMenu(menus.Menu):
    def __init__(self, embeds, **kwargs):
        super().__init__(**kwargs)
        self.embeds = embeds
        self.current_embed = 0

    @menus.button('🛡️')
    async def update_embed(self, _):
        self.current_embed = int(not self.current_embed)
        await self.message.edit(embed=self.embeds[self.current_embed])


class OldMembersSource(menus.ListPageSource):
    def format_page(self, menu, pages):
        embed = discord.Embed(
            title=_('OldMembers'),
            description=_('Estes são os membros mais antigos do servidor.'),
            color=config.MAIN_COLOR,
        )
        embed.set_footer(
            text=_(
                'Página {current} de {max}',
                current=menu.current_page + 1,
                max=self.get_max_pages(),
            )
        )
        embed.description = '\n'.join(pages)
        return embed


class Info(custom.Cog, translator=_):
    """Comandos de informações de objetos Discord."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def avatar(self, ctx, member: MemberOrUser = None):
        """
        Mostra o avatar de um usuário.

        O usuário não precisa estar no servidor.
        """
        if member is None:
            member = ctx.author

        embed = discord.Embed(color=config.MAIN_COLOR, description='')
        embed.set_author(
            name=_('Avatar de {member}', member=member.display_name),
            icon_url=member.avatar_url,
        )

        formats = ['png', 'jpg', 'webp']
        if member.is_avatar_animated():
            formats.append('gif')

        for fmt in formats:
            embed.description += f'[`{fmt.upper()}`]({member.avatar_url_as(format=fmt)}) '

        embed.set_image(url=member.avatar_url)

        await ctx.send(embed=embed)

    @avatar.command()
    @commands.guild_only()
    @needs_chunk()
    async def random(self, ctx):
        """Mostra um avatar aleatório."""
        member = choice(ctx.guild.members)
        await self.avatar(ctx, member)

    @commands.command()
    async def userinfo(self, ctx, member: MemberOrUser = None):
        """
        Mostra informações de um usuário.

        O usuário não precisa estar no servidor.
        """
        if member is None:
            member = ctx.author

        embed_info = discord.Embed(color=member.color)
        embed_info.set_author(name=f'{member} [{member.id}]', icon_url=member.avatar_url)

        embed_info.add_field(
            name=_('🗓️ Criou a conta em'),
            value=format_datetime(member.created_at),
            inline=False,
        )
        if isinstance(member, discord.Member):
            embed_info.add_field(
                name=_('🗓️ Entrou no servidor em'),
                value=format_datetime(member.joined_at),
                inline=False,
            )

            if ps := member.premium_since:
                embed_info.add_field(
                    name=_('♦️ Impulsionando desde'),
                    value=format_datetime(ps),
                    inline=False,
                )

            roles = [r.mention for r in reversed(member.roles) if r.id != ctx.guild.id]
            if not roles:
                roles = [_('Nenhum.')]

            embed_info.add_field(name=_('🛠️ Cargos'), value=format_list(roles), inline=False)

        msg = await ctx.send(embed=embed_info)
        if not isinstance(member, discord.Member):
            return

        embed_perms = discord.Embed(color=member.color)
        embed_perms.set_author(name=member, icon_url=member.avatar_url)

        perms = [str(PERMISSIONS[k]) for k, v in member.permissions_in(ctx.channel) if v]

        if not perms:
            perms = [_('Nenhuma.')]

        embed_perms.add_field(name=_('🛡️ Permissões'), value=format_list(perms), inline=False)

        menu = UserinfoMenu(
            (embed_info, embed_perms),
            timeout=60,
            message=msg,
            check_embeds=True,
        )
        await menu.start(ctx=ctx)

    @commands.command()
    @commands.guild_only()
    @needs_chunk()
    async def oldmembers(self, ctx):
        async with ctx.typing():

            def mapper(member):
                idx, member = member
                you = ' - ' + _('Você') if member == ctx.author else ''
                return f'`{idx+1}º` — `{member}`' + you

            members = map(
                mapper,
                enumerate(sorted(ctx.guild.members, key=lambda m: m.joined_at)),
            )

        source = OldMembersSource(tuple(members), per_page=10)
        pages = menus.MenuPages(source=source, clear_reactions_after=True)
        await pages.start(ctx)


def setup(bot):
    bot.add_cog(Info(bot))
