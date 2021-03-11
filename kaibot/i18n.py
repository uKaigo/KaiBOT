# Inspired by Cog-Creators/Red-DiscordBot, bot not copied from them.
import gettext
from contextvars import ContextVar

current_language = ContextVar('current_language', default='pt_BR')


class Translator:
    def __init__(self, name):
        self.__domain = name.split('.')[-1]
        self.__cache = dict()

    def __call__(self, message, *args, **kwargs):
        lang = current_language.get()
        if lang == 'pt_BR':
            # Since the bot is written in pt_BR, no need to translate
            # it.
            if args or kwargs:
                return message.format(*args, **kwargs)
            return message

        if lang not in self.__cache:
            self.__cache[lang] = gettext.translation(
                self.__domain,
                '../locales',
                languages=[lang],
                fallback=True
            )
        translated = self.__cache[lang].gettext(message)
        if args or kwargs:
            translated = translated.format(*args, **kwargs)

        return translated
