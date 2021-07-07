import sys

import discord
import discord.http
from discord.ext import commands

from .. import config
from ..i18n import Translator
from ..utils import custom
from ..utils.views import Confirm
from .games.ttt import TTTView

_ = Translator(__name__)


class Fun(custom.Cog, translator=_):
    """Comandos de diversão."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['tictactoe', 'jogodavelha', 'jdv'])
    @commands.guild_only()
    @commands.bot_has_permissions(add_reactions=True)
    async def ttt(self, ctx, player: discord.Member):
        """Começa um jogo da velha."""
        if player.bot:
            return await ctx.send(_('O outro jogador não pode ser um bot.'))
        if ctx.author == player:
            return await ctx.send(_('Você não pode jogar com você mesmo.'))

        text = _(
            '{player}, deseja jogar Jogo da Velha contra {author}?',
            author=ctx.author.mention,
            player=player.mention,
        )

        confirm_view = Confirm(player, timeout=60)

        msg = await ctx.send(text, view=confirm_view)

        await confirm_view.wait()

        if confirm_view.value is None:
            return await msg.edit(content=text + '\n- ' + _('Tempo excedido.'))
        elif confirm_view.value is False:
            not_accepted_text = _('{player} não aceitou.', player=player.mention)
            return await msg.edit(content=text + '\n -' + not_accepted_text)

        await msg.edit(
            content=_('Vez de {player}.', player=ctx.author.mention),
            view=TTTView(msg, (ctx.author, player)),
        )

    async def _create_application_invite(self, channel_id, application_id, app_name):
        # We're making the request ourselves because d.py doesn't
        # support this (only in 2.0).
        route = discord.http.Route('POST', '/channels/{channel_id}/invites', channel_id=channel_id)
        payload = {'target_type': 2, 'target_application_id': str(application_id)}
        return await self.bot.http.request(
            route, json=payload, reason=_('Criando sessão de {name}', name=app_name)
        )

    # I don't think these aliases are good, but idk another name.
    @commands.command(aliases=['ytt', 'youtubetogether'])
    @commands.bot_has_guild_permissions(create_instant_invite=True)
    async def watchyt(self, ctx, voice_channel: discord.VoiceChannel):
        """
        Cria uma nova sessão de YouTube Together.

        Apenas disponível em desktop.
        """
        invite_data = await self._create_application_invite(
            voice_channel.id, 755600276941176913, 'YouTube Together'
        )

        embed = discord.Embed(
            description=_(
                '[Clique aqui]({invite}) para abrir a sessão de {name}.',
                name='YouTube Together',
                invite=f'https://discord.gg/{invite_data["code"]}',
            ),
            color=config.MAIN_COLOR,
        )

        return await ctx.send(embed=embed)

    @commands.command(aliases=['pn', 'pokernight'])
    @commands.bot_has_guild_permissions(create_instant_invite=True)
    async def poker(self, ctx, voice_channel: discord.VoiceChannel):
        """
        Cria uma nova sessão de Poker Night.

        Apenas disponível em desktop.
        """
        invite_data = await self._create_application_invite(
            voice_channel.id, 755827207812677713, 'Poker Night'
        )

        embed = discord.Embed(
            description=_(
                '[Clique aqui]({invite}) para abrir a sessão de {name}.',
                name='Poker Night',
                invite=f'https://discord.gg/{invite_data["code"]}',
            ),
            color=config.MAIN_COLOR,
        )

        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))


def teardown(bot):
    sys.modules.pop('kaibot.cogs.games.ttt')
