from random import choice
from typing import Union

import discord
from discord.ext import commands, menus
from babel.dates import format_date, format_time
from discord.member import Member

from .. import config
from ..utils.decorators import needs_chunk
from ..utils.converters import MemberOrUser
from ..utils.translations import PERMISSIONS
from ..i18n import Translator, get_babel_locale


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


class Info(commands.Cog):
    """Comandos de informações de objetos Discord."""

    def __init__(self, bot):
        self.bot = bot

    def _format_datetime(self, datetime, date_fmt='medium', time_fmt='short'):
        locale = get_babel_locale()
        return _(
            '{date} às {time}',
            date=format_date(datetime, date_fmt, locale),
            time=format_time(datetime, time_fmt, None, locale)
        ).capitalize()

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
            icon_url=member.avatar_url
        )

        formats = ['png', 'jpg', 'webp']
        if member.is_avatar_animated():
            formats.append('gif')

        for fmt in formats:
            embed.description += f'[`{fmt.upper()}`]({member.avatar_url_as(format=fmt)}) '

        embed.set_image(url=member.avatar_url)

        return await ctx.send(embed=embed)

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
        embed_info.set_author(name=member, icon_url=member.avatar_url)

        embed_info.add_field(name=_('🔢 ID'), value=member.id)

        embed_info.add_field(
            name=_('🗓️ Criou a conta em'),
            value=self._format_datetime(member.created_at),
            inline=False
        )
        if isinstance(member, discord.Member):
            embed_info.add_field(
                name=_('🗓️ Entrou no servidor em'),
                value=self._format_datetime(member.joined_at),
                inline=False
            )

            roles = [r.mention for r in reversed(member.roles) if r.id != ctx.guild.id]
            roles.append('@everyone')

            embed_info.add_field(name=_('🛠️ Cargos'), value=', '.join(roles), inline=False)

        msg = await ctx.send(embed=embed_info)
        if not isinstance(member, discord.Member):
            return

        embed_perms = discord.Embed(color=member.color)
        embed_perms.set_author(name=member, icon_url=member.avatar_url)

        perms = (f'`{PERMISSIONS[k]}`' for k, v in member.permissions_in(ctx.channel) if v)

        embed_perms.add_field(name=_('🛡️ Permissões'), value=', '.join(perms), inline=False)

        menu = UserinfoMenu((embed_info, embed_perms), timeout=60, message=msg, check_embeds=True)
        await menu.start(ctx=ctx, wait=True)


def setup(bot):
    bot.add_cog(Info(bot))
