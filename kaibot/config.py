DEFAULT_LANGUAGE = 'pt_BR'

PREFIXES = ('k.', 'kaibot ')

INTENTS = ('guilds', 'messages', 'reactions', 'members')

MAIN_COLOR = 0xFF6EFF

JISHAKU_FLAGS = ('HIDE', 'NO_DM_TRACEBACK', 'NO_UNDERSCORE')
EXTENSIONS = (
    'jishaku',
    '.cogs.bot_events',
    '.cogs.misc',
    '.cogs.info',
    '.cogs.error_handler',
    '.cogs.fun',
    '.cogs.utilities',
    '.cogs.moderation',
)

PRIVATE_GUILD = 795383343248048189
FLAGS = {833710346316677130: 1, 844290546624888842: 2, 831169250978562069: 4}
LOGS = {'commands': 822644877673496626, 'errors': 822644820170113057, 'guilds': 842229415223623682}

__import__('os').environ.update({f'JISHAKU_{FLAG}': '1' for FLAG in JISHAKU_FLAGS})
