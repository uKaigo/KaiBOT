from babel.dates import format_date as _fmt_date, format_time as _fmt_time
from babel.lists import format_list as _fmt_list

from ..i18n import Translator, get_babel_locale

_ = Translator(__name__)


def format_datetime(datetime, date_fmt='medium', time_fmt='short'):
    locale = get_babel_locale()
    return _(
        '{date} às {time}',
        date=_fmt_date(datetime, date_fmt, locale),
        time=_fmt_time(datetime, time_fmt, None, locale),
    ).capitalize()


def format_list(lst, style='standard'):
    locale = get_babel_locale()
    return _fmt_list(tuple(lst), style, locale)
