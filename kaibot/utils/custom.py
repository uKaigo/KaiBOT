from discord.ext import commands

from ..i18n import Translator


class _Cmd(commands.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.translator = kwargs.pop('translator', Translator._noop)


class CogAttrMeta(commands.CogMeta):
    """Adds the translator kwarg."""

    def __new__(cls, name, bases, attrs, **kwargs):
        translator = kwargs.pop('translator', Translator._noop)
        attrs['__translator__'] = translator

        for aname, attr in attrs.items():
            if isinstance(attr, commands.Command):
                # Dinamically create the class so we don't break the
                # cls kwarg.
                cmd_cls = type(
                    attr.__class__.__name__, (_Cmd, attr.__class__), {}
                )

                kwgs = attr.__original_kwargs__ | {'translator': translator}
                new_attr = cmd_cls(attr.callback, **kwgs)

                attr._ensure_assignment_on_copy(new_attr)
                attrs[aname] = new_attr

        return super().__new__(cls, name, bases, attrs, **kwargs)


class Cog(commands.Cog, metaclass=CogAttrMeta):
    pass
