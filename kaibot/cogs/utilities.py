import re
import json
import sys
import asyncio
from random import randint
from functools import cached_property

import discord
from discord.ext import commands
from aiohttp import ClientConnectorError

from .. import config
from ..i18n import Translator
from ..utils import custom, format_list
from ..utils.decorators import in_executor
from .resources.brainfuck import BrainfuckDecoder

_ = Translator(__name__)


class Utilities(custom.Cog, translator=_):
    """Comandos úteis."""

    DICE_REGEX = re.compile(r'((?P<count>\d*)d)?(?P<sides>\d+(?!\d*d))')  # Regex Sucks
    # Includes: 0-9 a-z A-Z
    BF_INPUT = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

    def __init__(self, bot):
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

        # FIXME: Really. Fix this mess.
        description = ''
        async with ctx.typing():
            try:
                dest = await self.bot.session.get(link.strip('<>'))
            except ClientConnectorError as e:
                return await ctx.send(
                    _('Não pude me conectar com o site: `{error}`', error=e.strerror)
                )

            h_len = len(dest.history)
            for index, res in enumerate(dest.history + (dest,)):
                em = '🔷' if index in (0, h_len) else '🔹'
                description += f'{em} `{res.status}` - {res.url}\n'

        embed.description = description

        return await ctx.send(embed=embed)

    @in_executor
    def _convert_to_vaporwave(self, text):
        output = ''
        for char in text:
            if 36 <= ord(char) <= 126:
                # FF01 is the start of vaporwave "font".
                output += chr(ord(char) - 33 + 0xFF01)
            else:
                output += char
        return output

    @commands.command()
    async def vaporwave(self, ctx, *, text):
        """Transforma o texto em ｖａｐｏｒｗａｖｅ."""
        author_notes = f'\n\n> {_("Texto por: {author}", author=ctx.author.mention)}'
        max_len = 2000 - len(author_notes)
        if len(text) > max_len:
            return await ctx.send(_('O texto pode ter no máximo {max} caracteres.', max=max_len))

        async with ctx.typing():
            converted = await self._convert_to_vaporwave(text)

        await ctx.send(converted + author_notes)

    @commands.group(invoke_without_command=True)
    async def brainfuck(self, ctx):
        """Tradutor de [brainfuck](https://pt.wikipedia.org/wiki/Brainfuck)."""
        await ctx.send_help(self.brainfuck)

    @brainfuck.command(name='decode')
    @commands.max_concurrency(1, commands.BucketType.member)
    async def brainfuck_decode(self, ctx, *, text):
        """
        Decodificador de [brainfuck](https://pt.wikipedia.org/wiki/Brainfuck).

        `,` lerá o próximo valor de uma string `A-Za-z0-9`.
        Por exemplo: `,.` imprimiria "A".
        """
        decoder = BrainfuckDecoder(self.BF_INPUT)
        runner = in_executor(decoder)

        try:
            async with ctx.typing():
                out = await asyncio.wait_for(runner(text), timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(_('Tempo excedido.'))

            decoder.cancelled = True
            await asyncio.sleep(0.3)  # Let decoder cancel
            return decoder.mem.clear()

        mem = json.dumps(decoder.mem, indent=2, check_circular=False).replace('"', '')

        embed = discord.Embed(title='Brainfuck', color=config.MAIN_COLOR)
        embed.set_footer(
            text=_('Texto por: {author} ({author.id})', author=ctx.author),
            icon_url=ctx.author.avatar,
        )
        if out.strip():
            embed.add_field(name=_('Saída:'), value=out, inline=False)
        embed.add_field(name=_('Memória:'), value=f'```py\n{mem}```', inline=False)

        return await ctx.send(embed=embed)

    # TODO: Brainfuck Encode?

    @commands.group(invoke_without_command=True)
    async def encrypt(self, ctx, criptography, text):
        """Comandos para criptografar um texto."""
        await ctx.send_help(self.encrypt)

    @commands.group(invoke_without_command=True)
    async def decrypt(self, ctx, criptography, code):
        """Comandos para descriptografar um código."""
        await ctx.send_help(self.decrypt)

    # MORSE #

    @cached_property
    def morse_table(self):
        with open('cogs/resources/morse.jsonc') as f:
            to_parse = re.sub('//.+', '', f.read())
            return json.loads(to_parse)

    @cached_property
    def inverted_morse_table(self):
        return dict(zip(self.morse_table.values(), self.morse_table.keys()))

    @encrypt.command(name='morse')
    async def encrypt_morse(self, ctx, *, text: str.split):
        """Criptografar código morse."""
        final = ''
        for word in text:
            for char in word:
                try:
                    final += self.morse_table[char.upper()] + ' '
                except KeyError:
                    pass

            final += ' / '

        author_notes = f'\n\n> {_("Texto por: {author}", author=ctx.author.mention)}'
        await ctx.send(final[:-2] + author_notes)

    @decrypt.command(name='morse')
    async def decrypt_morse(self, ctx, *, code):
        """Descriptografar código morse."""
        final = ''
        code = code.split('/')

        for word in code:
            for char in word.split():
                try:
                    final += self.inverted_morse_table[char]
                except KeyError:
                    pass
            final += ' '

        author_notes = f'\n\n> {_("Texto por: {author}", author=ctx.author.mention)}'
        await ctx.send(final + author_notes)


def setup(bot):
    bot.add_cog(Utilities(bot))


def teardown(bot):
    sys.modules.pop('kaibot.cogs.resources.brainfuck')
