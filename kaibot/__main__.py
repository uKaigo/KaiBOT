import logging
import os
import sys
import argparse
from pathlib import Path

from dotenv import load_dotenv

from .logging import config_logging
from .bot import KaiBOT
from .utils import get_intents_from

log = logging.getLogger('kaibot.main')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t',
        '--token',
        help='Run with the given token.'
    )
    parser.add_argument(
        '--intents',
        help='Run with custom intents.',
        nargs='+'
    )
    return parser.parse_args()


def main():
    options = parse_args()
    if not options.token:
        options.token = os.getenv('DISCORD_TOKEN')
        if not options.token:
            raise RuntimeError('Token must be set.')

    intents = None
    if options.intents:
        intents = get_intents_from(options.intents)

    if intents:
        bot = KaiBOT(intents=intents, chunk_guilds_at_startup=False)
    else:
        bot = KaiBOT(chunk_guilds_at_startup=False)
    bot.run(options.token)


if __name__ == '__main__':
    config_logging({'file': logging.DEBUG, 'stdout': logging.INFO}, location=Path('logs'))

    log.debug('Changing dir to "kaibot".')
    os.chdir('kaibot')

    load_dotenv()

    try:
        main()
    except:
        log.critical('Unhandled error occurred.', exc_info=True)
        sys.exit(1)
    else:
        sys.exit(0)
    finally:
        log.info('Quitting...')
