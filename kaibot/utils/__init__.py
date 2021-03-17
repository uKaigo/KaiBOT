from discord import Intents


def get_intents_from(iter_):
    """Get the intents object from List[str]."""
    return Intents(**{intent: True for intent in iter_})
