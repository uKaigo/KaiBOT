import re
from random import randint

import discord
import discord.http
from discord.ext import commands

from .. import config
from ..i18n import Translator
from ..utils import custom, format_list

_ = Translator(__name__)


class Utilities(custom.Cog, translator=_):
    """Comandos úteis."""

    def __init__(self, bot):
        self.DICE_REGEX = re.compile(r'((?P<count>\d*)d)?(?P<sides>\d+(?!\d*d))')  # Regex Sucks
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, dice='d20'):
        """
        Rola um dado.

        Explicação (`count`d`sides`):
        `5d100` irá rodar 5 dados de 100 lados.
        `d100` irá rodar 1 dado de 100 lados.
        `100` irá rodar 1 dado de 100 lados.
        """
        match = self.DICE_REGEX.match(dice)
        if not match:
            return await ctx.send_help(ctx.command)

        count = int(match.group('count') or 1)
        sides = int(match.group('sides'))

        if 0 in (count, sides):
            return await ctx.send(_('Nenhum dos valores pode ser 0.'))
        if sides == 1:
            return await ctx.send(_('O dado não pode ter somente 1 lado.'))
        if sides > 1000:
            return await ctx.send(_('O dado precisa ter menos que 1000 lados.'))
        if count > 200:
            return await ctx.send(_('Você pode rolar no máximo 200 dados por vez.'))

        results = []
        for i in range(count):
            results.append(randint(1, sides))

        if count == 1:
            return await ctx.send(_('Seu dado resultou em: {result}', result=results[0]))

        return await ctx.send(
            _('Seus dados resultaram em: {results}', results=format_list(results))
            + '\n\n'
            + _('Soma: {sum}', sum=sum(results))
        )

    @commands.command()
    async def resolve(self, ctx, link):
        """Mostra todos os redirecionamentos do link."""
        embed = discord.Embed(title=_('Redirecionamentos'), color=config.MAIN_COLOR)

        if not link.strip('<>').startswith(('http://', 'https://')):
            link = 'http://' + link

        description = ''
        async with ctx.typing():
            dest = await self.bot.session.get(link.strip('<>'))
            h_len = len(dest.history)
            for index, res in enumerate(dest.history + (dest,)):
                em = '🔷' if index in (0, h_len) else '🔹'
                description += f'{em} `{res.status}` - {res.url}\n'

        embed.description = description

        return await ctx.send(embed=embed)

    async def _create_application_invite(self, channel_id, application_id, app_name):
        # We're making the request ourselves because d.py doesn't
        # support this.
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
    bot.add_cog(Utilities(bot))
