from discord import Intents


def get_intents_from(iter_):
    return Intents(**{intent: True for intent in iter_})
