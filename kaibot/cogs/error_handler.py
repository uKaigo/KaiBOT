import io
import traceback
from logging import getLogger

import discord
from discord.ext import commands

from .. import config
from ..i18n import Translator
from ..utils import format_list

_ = Translator(__name__)
log = getLogger('kaibot.error_handler')


class ErrorHandler(commands.Cog):
    IGNORED_ERRORS = (commands.CommandNotFound, commands.NotOwner)

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        original = error.__cause__

        if isinstance(error, self.IGNORED_ERRORS):
            return

        if isinstance(error, commands.BadArgument):
            if 'int' in str(error):
                return await ctx.send(_('Insira um número válido.'))

        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.send(_('Este comando só pode ser executado em servidores.'))

        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command)

        if isinstance(error, commands.MemberNotFound):
            return await ctx.send(
                _(
                    'O membro "{string}" não foi encontrado.',
                    string=error.argument,
                )
            )

        if isinstance(error, commands.BadUnionArgument):
            CONVERTER_MAPPING = {
                discord.Member: _('membro'),
                discord.User: _('usuário'),
            }
            converters = [CONVERTER_MAPPING.get(c, c.__name__.lower()) for c in error.converters]

            arg = error.errors[0].argument

            return await ctx.send(
                _(
                    'Não foi possível converter "{string}" para {converters}.',
                    string=arg,
                    converters=format_list(converters, style='or'),
                )
            )

        err = original or error

        log.error(
            f'An error ocurred in the command "{ctx.command.qualified_name}". '
            f'Message ID: {ctx.message.id}.',
            exc_info=err,
        )

        embed = discord.Embed(
            title=f'Erro no comando "{ctx.command.qualified_name}"',
            description=f'ID da mensagem: {ctx.message.id}',
            color=config.MAIN_COLOR,
        )

        tb_exc = traceback.TracebackException.from_exception(err)

        paginator = commands.Paginator('```py\n', '```', 1024, '')
        for line in tb_exc.format():
            paginator.add_line(line)

        file = None
        if len(paginator) > 5850:  # Other texts needs to be <151 chrs.
            stream = io.StringIO(''.join(paginator.pages))
            file = discord.File(stream, 'error.txt')
        else:
            for page in paginator.pages:
                embed.add_field(name='\N{ZERO WIDTH SPACE}', value=page, inline=False)

        channel = self.bot.get_channel(config.LOGS['errors'])
        await channel.send(embed=embed, file=file)

        await ctx.send(
            _(
                'Ocorreu um erro ao executar este comando.\n'
                'Tente contatar o suporte para resolver o problema.\n\n'
                '{error}',
                error=f'```py\n{list(tb_exc.format(chain=False))[-1]}```',
            )
        )


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
