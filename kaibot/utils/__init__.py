def get_intents(intents):
    return tuple(str(i[0]) for i in intents if i[1])
