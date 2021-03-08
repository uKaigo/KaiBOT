import logging
import os
import sys
import argparse
from pathlib import Path

from .logging import config_logging
from .bot import KaiBOT

log = logging.getLogger('kaibot.main')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t',
        '--token',
        help='Run with the given token.'
    )
    return parser.parse_args()


def main():
    options = parse_args()
    if not options.token:
        options.token = os.getenv('DISCORD_TOKEN')
        if not options.token:
            raise RuntimeError('Token must be set.')

    bot = KaiBOT()

    bot.run(options.token)


if __name__ == '__main__':
    config_logging({'file': logging.DEBUG, 'stdout': logging.INFO}, location=Path('logs'))

    log.debug('Changing dir to "kaibot".')
    os.chdir('kaibot')

    try:
        main()
    except SystemExit:
        pass
    except:
        log.critical('Unhandled error occurred.', exc_info=True)
        sys.exit(1)
    else:
        sys.exit(0)
    finally:
        log.info('Quitting...')
