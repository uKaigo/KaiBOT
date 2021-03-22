import os
import traceback
from logging import getLogger

import discord
from discord.ext import commands

from .. import config
from ..i18n import Translator
from ..utils.formatters import format_list

_ = Translator(__name__)
log = getLogger('kaibot.error_handler')


class ErrorHandler(commands.Cog):
    IGNORED_ERRORS = (commands.CommandNotFound, commands.NotOwner)

    def __init__(self, bot):
        self.bot = bot
        self.webhook = discord.Webhook.from_url(
            os.environ['CMD_ERROR_WEBHOOK'],
            adapter=discord.AsyncWebhookAdapter(self.bot.session)
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = error.__cause__ or error

        if isinstance(error, self.IGNORED_ERRORS):
            return

        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.send(_('Este comando só pode ser executado em servidores.'))

        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command)

        if isinstance(error, commands.MemberNotFound):
            return await ctx.send(_(
                'O membro "{string}" não foi encontrado.',
                string=error.argument
            ))

        if isinstance(error, commands.BadUnionArgument):
            CONVERTER_MAPPING = {
                discord.Member: _('membro'),
                discord.User: _('usuário')
            }
            converters = [
                CONVERTER_MAPPING.get(c, c.__name__.lower())
                for c in error.converters
            ]

            arg = error.errors[0].argument

            return await ctx.send(_(
                'Não foi possível converter "{string}" para {converters}.',
                string=arg,
                converters=format_list(converters, style='or')
            ))

        log.error(f'An error ocurred in the command "{ctx.command.qualified_name}". '
                  f'Message ID: {ctx.message.id}.', exc_info=error)

        embed = discord.Embed(
            title=f'Erro no comando "{ctx.command.qualified_name}"',
            description=f'ID da mensagem: {ctx.message.id}',
            color=config.MAIN_COLOR
        )

        fmt = traceback.format_exception(None, error, error.__traceback__)
        embed.add_field(name='\N{ZERO WIDTH SPACE}', value=f"```py\n{''.join(fmt)}```")

        await self.webhook.send(embed=embed)

        await ctx.send(_(
            'Ocorreu um erro ao executar este comando.\n'
            'Tente contatar o suporte para resolver o problema.\n\n'
            '{error}',
            error=f'```py\n{fmt[-1]}```'
        ))


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
