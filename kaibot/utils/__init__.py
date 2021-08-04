from babel.lists import format_list as _fmt_list
from discord import Intents, Member
from discord.utils import escape_mentions, escape_markdown

from ..i18n import get_babel_locale


def get_intents_from(iter_):
    """Get the intents object from List[str]."""
    return Intents(**{intent: True for intent in iter_})


def format_list(lst, style='standard'):
    locale = get_babel_locale()
    return _fmt_list(tuple(lst), style, locale)


def escape_text(text):
    return escape_markdown(escape_mentions(str(text)))


def can_modify(member, target):
    guild = member.guild
    if member == guild.owner or not isinstance(target, Member):
        return True

    if guild.owner == target or member.top_role <= target.top_role:
        return False

    return True
