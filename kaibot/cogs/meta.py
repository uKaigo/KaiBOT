from discord.ext import commands

from ..i18n import Translator

_ = Translator(__name__)


class Meta(commands.Cog):
    """Comandos diversos."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Envia a latência da websocket e o tempo de resposta."""
        txt = _(
            '🏓 Ping\n'
            '- Websocket: {}ms\n'
            '- Tempo de resposta: {}ms'
        )
        msg = await ctx.send(txt.format('NaN', 'NaN'))
        diff = (msg.created_at - ctx.message.created_at).total_seconds()

        await msg.edit(content=txt.format(int(self.bot.latency * 1000), int(diff * 1000)))


def setup(bot):
    bot.add_cog(Meta(bot))
