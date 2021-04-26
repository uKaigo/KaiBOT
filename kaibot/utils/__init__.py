from babel.dates import format_date as _fmt_date
from babel.dates import format_time as _fmt_time
from babel.lists import format_list as _fmt_list
from discord import Intents
from discord.utils import escape_mentions, escape_markdown

from ..i18n import get_babel_locale
from .translations import DATETIME


def get_intents_from(iter_):
    """Get the intents object from List[str]."""
    return Intents(**{intent: True for intent in iter_})


def format_datetime(datetime, date_fmt='medium', time_fmt='short'):
    locale = get_babel_locale()
    return str(DATETIME).format(
        date=_fmt_date(datetime, date_fmt, locale),
        time=_fmt_time(datetime, time_fmt, None, locale),
    )


def format_list(lst, style='standard'):
    locale = get_babel_locale()
    return _fmt_list(tuple(lst), style, locale)


def escape_text(text):
    return escape_markdown(escape_mentions(text))
