import discord
from discord.ext import commands

from ..i18n import Translator


class _Cmd(commands.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.translator = kwargs.pop('translator')


class _CogAttrMeta(commands.CogMeta):
    """Adds the translator kwarg."""

    def __new__(cls, *args, **kwargs):
        name, bases, attrs = args
        translator = kwargs.pop('translator', Translator._noop)
        if not translator:
            return super().__new__(cls, name, bases, attrs, **kwargs)
        attrs['__translator__'] = translator

        for aname, attr in attrs.items():
            if isinstance(attr, commands.Command):
                # Dinamically create the class so we don't break the
                # cls kwarg.
                cmd_cls = type(attr.__class__.__name__, (_Cmd, attr.__class__), {})

                kwgs = attr.__original_kwargs__ | {'translator': translator}
                new_attr = cmd_cls(attr.callback, **kwgs)

                attr._ensure_assignment_on_copy(new_attr)
                attrs[aname] = new_attr
        return super().__new__(cls, name, bases, attrs, **kwargs)


class Cog(commands.Cog, metaclass=_CogAttrMeta):
    pass


class View(discord.ui.View):
    """
    Custom view that handles errors.

    Since we can't access the bot instance from inside the view, this
    is defined by the ErrorHandler, which can.

    TODO: Use contextvars to get the bot.
    """

    _underlying_error_handler = None

    def on_error(self, error, item, interaction):
        if self._underlying_error_handler:
            return self._underlying_error_handler(self, error, item, interaction)
        return super().on_error(error, item, interaction)
