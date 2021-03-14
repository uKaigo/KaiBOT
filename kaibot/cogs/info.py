import discord
from discord.ext import commands

from .. import config
from ..i18n import Translator

_ = Translator(__name__)


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        """Envia o avatar do membro, ou do autor."""
        if member is None:
            member = ctx.author

        embed = discord.Embed(color=config.MAIN_COLOR, description='')
        embed.set_author(
            name=_('Avatar de {member}', member=member.display_name),
            icon_url=member.avatar_url
        )

        formats = ('png', 'jpg', 'webp', 'gif')

        for fmt in formats:
            embed.description += f'[`{fmt.upper()}`]({member.avatar_url_as(format=fmt)}) '

        embed.set_image(url=member.avatar_url)

        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
