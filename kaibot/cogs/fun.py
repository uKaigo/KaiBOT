import asyncio
import sys
from asyncio import TimeoutError

import discord
import discord.http
from discord.ext import commands

from .. import config
from ..i18n import Translator
from ..utils import custom, escape_text
from .games.ttt import TTTIntegration

_ = Translator(__name__)


class Fun(custom.Cog, translator=_):
    """Comandos de diversão."""

    def __init__(self, bot):
        self.bot = bot
        self._ttt_game = TTTIntegration(bot)
        self.waiting = []

    def cog_unload(self):
        self._ttt_game.destroy()

    async def _send_confirmation(self, channel_id, text):
        route = discord.http.Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
        payload = {'content': text}
        payload['components'] = [
            {
                'type': 1,
                'components': [
                    {'label': _('Sim'), 'style': 3, 'custom_id': 'choice_1', 'type': 2},
                    {'label': _('Não'), 'style': 4, 'custom_id': 'choice_0', 'type': 2},
                ],
            }
        ]

        data = await self.bot.http.request(route, json=payload)
        return data['id']

    async def _get_confirmation(self, msg_id, player):
        while True:
            event = await self.bot.wait_for('socket_response', timeout=60)

            if event['t'] != 'INTERACTION_CREATE':
                continue

            payload = event['d']

            route = discord.http.Route(
                'POST',
                '/interactions/{interaction_id}/{interaction_token}/callback',
                interaction_id=payload['id'],
                interaction_token=payload['token'],
            )
            to_send = {'type': 6}

            # ACK
            await self.bot.http.request(route, json=to_send)

            try:
                if payload['message']['id'] != str(msg_id):
                    continue

                if payload['member']['user']['id'] != str(player.id):
                    continue
            except KeyError as e:
                continue

            choice = payload['data']['custom_id'][7:]

            return int(choice)

    @commands.command(aliases=['tictactoe', 'jogodavelha', 'jdv'])
    @commands.guild_only()
    @commands.bot_has_permissions(add_reactions=True)
    async def ttt(self, ctx, player: discord.Member):
        """Começa um jogo da velha."""
        if player.bot:
            return await ctx.send(_('O outro jogador não pode ser um bot.'))
        if ctx.author == player:
            return await ctx.send(_('Você não pode jogar com você mesmo.'))
        if ctx.author.id in self._ttt_game:
            return await ctx.send(_('Você já está em um jogo.'))
        if player.id in self._ttt_game or player.id in self.waiting:
            return await ctx.send(
                _('**{player}** já está em um jogo.', player=escape_text(player.display_name))
            )

        text = _(
            '{player}, deseja jogar Jogo da Velha contra {author}?',
            author=ctx.author.mention,
            player=player.mention,
        )
        msg_id = await self._send_confirmation(ctx.channel.id, text)
        msg = self.bot._connection._get_message(int(msg_id))

        try:
            self.waiting.append(player.id)
            choice = await asyncio.wait_for(self._get_confirmation(msg.id, player), timeout=60)
        except TimeoutError:
            return await msg.edit(content=text + '\n- ' + _('Tempo excedido.'))
        finally:
            self.waiting.remove(player.id)

        if choice == 0:
            not_accepted_text = _('{player} não aceitou.', player=player.mention)
            return await msg.edit(content=text + '\n- ' + not_accepted_text)

        await self._ttt_game.start(msg, ctx.author, player)

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
