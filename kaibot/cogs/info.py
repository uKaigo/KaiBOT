from random import choice

import discord
from discord.utils import format_dt
from discord.ext import commands

from .. import config
from ..i18n import Translator
from ..utils import custom, format_list
from ..utils.converters import MemberOrUser
from ..utils.decorators import needs_chunk
from ..utils.translations import PERMISSIONS
from ..utils.enums import Flags
from ..utils.views import PaginatorView

_ = Translator(__name__)


class UserinfoView(custom.View):
    def __init__(self, embeds, **kwargs):
        super().__init__(**kwargs)
        self.current = 0
        self.embeds = embeds

        # TODO: Think of better emojis.
        self.buttons = [
            {'label': _('Permissões'), 'emoji': '🛡️'},
            {'label': _('Informações'), 'emoji': '👤'},
        ]

        self.toggle_perms.label = self.buttons[0]['label']
        self.toggle_perms.emoji = self.buttons[0]['emoji']

        self.message = None

    @discord.ui.button()
    async def toggle_perms(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current ^= 1
        button_info = self.buttons[self.current]

        button.label = button_info['label']
        button.emoji = button_info['emoji']

        await interaction.response.edit_message(embed=self.embeds[self.current], view=self)

    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None)


class OldmembersView(PaginatorView):
    def __init__(self, message, members, *, per_page=10, **kwargs):
        super().__init__(message=message, **kwargs)
        self.pages = tuple(members[i : i + per_page] for i in range(0, len(members), per_page))

    def get_max_pages(self):
        return len(self.pages)

    async def show_current_page(self):
        embed = discord.Embed(
            title=_('OldMembers'),
            description=_('Estes são os membros mais antigos do servidor.'),
            color=config.MAIN_COLOR,
        )
        embed.set_footer(
            text=_(
                'Página {current} de {max}',
                current=self.current_page + 1,
                max=self.get_max_pages(),
            )
        )
        embed.description = '\n'.join(self.pages[self.current_page])

        self.go_to_first.disabled = self.current_page == 0
        self.go_to_previous.disabled = self.current_page == 0
        self.go_to_last.disabled = self.current_page == self.get_max_pages() - 1
        self.go_to_next.disabled = self.current_page == self.get_max_pages() - 1

        await self.message.edit(embed=embed, view=self)


class Info(custom.Cog, translator=_):
    """Comandos de informações."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def avatar(self, ctx, *, member: MemberOrUser = None):
        """
        Mostra o avatar de um usuário.

        O usuário não precisa estar no servidor.
        """
        if member is None:
            member = ctx.author

        embed = discord.Embed(color=config.MAIN_COLOR, description='')
        embed.set_author(
            name=_('Avatar de {member}', member=member.display_name),
            icon_url=member.avatar,
        )
        embed.set_footer(text=_('Executado por: {author}', author=ctx.author))

        formats = ['png', 'jpg', 'webp']
        if member.avatar.is_animated():
            formats.append('gif')

        for fmt in formats:
            embed.description += f'[`{fmt.upper()}`]({member.avatar.with_format(fmt)}) '

        embed.set_image(url=member.avatar)

        await ctx.send(embed=embed)

    @avatar.command(name='random')
    @commands.guild_only()
    @needs_chunk()
    async def avatar_random(self, ctx):
        """Mostra um avatar aleatório."""
        member = choice(ctx.guild.members)
        await self.avatar(ctx, member=member)

    @commands.command()
    async def userinfo(self, ctx, *, member: MemberOrUser = None):
        """
        Mostra informações de um usuário.

        O usuário não precisa estar no servidor.
        """
        if member is None:
            member = ctx.author

        embed_info = discord.Embed(color=member.color)
        embed_info.set_author(name=f'{member} [{member.id}]', icon_url=member.avatar)

        flags = []
        user_flags = self.bot.get_flags_for(member)

        if user_flags & Flags.DEVELOPER:
            flags.append('💻  ' + _('Desenvolvedor'))
        if user_flags & Flags.TRANSLATOR:
            flags.append('📖  ' + _('Tradutor'))
        if user_flags & Flags.VIP:
            flags.append('⭐  ' + _('VIP'))

        embed_info.description = '\n'.join(flags)

        embed_info.add_field(
            name=_('🗓️ Criou a conta em'),
            value=format_dt(member.created_at, 'f'),
            inline=False,
        )
        if isinstance(member, discord.Member):
            embed_info.add_field(
                name=_('🗓️ Entrou no servidor em'),
                value=format_dt(member.joined_at, 'f'),
                inline=False,
            )

            if ps := member.premium_since:
                embed_info.add_field(
                    name=_('♦️ Impulsionando desde'),
                    value=format_dt(ps, 'f'),
                    inline=False,
                )

            roles = [r.mention for r in reversed(member.roles) if r.id != ctx.guild.id]
            if not roles:
                roles = [_('Nenhum.')]

            embed_info.add_field(name=_('🛠️ Cargos'), value=format_list(roles), inline=False)
        else:
            return await ctx.send(embed=embed_info)

        embed_perms = discord.Embed(color=member.color)
        embed_perms.set_author(name=f'{member} [{member.id}]', icon_url=member.avatar)

        perms = [str(PERMISSIONS[k]) for k, v in ctx.channel.permissions_for(member) if v]

        if not perms:
            perms = [_('Nenhuma.')]

        embed_perms.add_field(name=_('🛡️ Permissões'), value=format_list(perms), inline=False)

        view = UserinfoView((embed_info, embed_perms), timeout=60)
        msg = await ctx.send(embed=embed_info, view=view)
        view.message = msg

    @commands.command()
    @commands.guild_only()
    @needs_chunk()
    async def oldmembers(self, ctx):
        """Mostra os membros mais antigos do servidor."""
        async with ctx.typing():

            def mapper(idx_member):
                idx, member = idx_member
                you = f' - {_("Você")}' if member == ctx.author else ''
                return f'`{idx+1}º` — `{member}`' + you

            members = map(
                mapper,
                enumerate(sorted(ctx.guild.members, key=lambda m: m.joined_at)),
            )

        msg = await ctx.send('\N{ZERO WIDTH SPACE}')
        view = OldmembersView(msg, tuple(members), timeout=60)
        await view.show_current_page()


def setup(bot):
    bot.add_cog(Info(bot))
