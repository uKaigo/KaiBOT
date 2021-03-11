from discord.ext import commands


class Meta(commands.Cog):
    """Comandos diversos."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Envia a latência da websocket e o tempo de resposta."""
        txt = (
            '🏓 Ping\n'
            '- Websocket: {}ms\n'
            '- Tempo de resposta: {}ms'
        )
        msg = await ctx.send(txt.format('NaN', 'NaN'))
        diff = (msg.created_at - ctx.message.created_at).total_seconds()

        data = (int(self.bot.latency * 1000), int(diff * 1000))

        await msg.edit(content=txt.format(*data))


def setup(bot):
    bot.add_cog(Meta(bot))
