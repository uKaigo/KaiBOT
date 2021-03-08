from discord import Intents


def get_selected_intents(intents):
    return tuple(str(i[0]) for i in intents if i[1])


def get_intents_from(intents_iter):
    return Intents(**{intent: True for intent in intents_iter})
