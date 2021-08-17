import argparse
import logging
import os
import sys
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from .bot import KaiBOT
from .logging import config_logging
from .scripts import mo_compiler as compile_mo

log = logging.getLogger('kaibot.main')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', help='Run with the given token.')
    return parser.parse_args()


async def main():
    options = parse_args()
    if not options.token:
        options.token = os.getenv('DISCORD_TOKEN')
        if not options.token:
            raise RuntimeError('Token must be set with flag or DISCORD_TOKEN env.')

    bot = KaiBOT(chunk_guilds_at_startup=False)
    try:
        await bot.start(options.token)
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == '__main__':
    config_logging({'file': logging.DEBUG, 'stdout': logging.INFO}, location=Path('logs'))

    log.debug('Changing dir to "kaibot".')
    os.chdir('kaibot')

    load_dotenv()

    log.info('Compiling mo...')

    compile_mo.log.setLevel(logging.WARNING)
    compile_mo.main(Path('../locales'))

    log.info('Compiled.')

    try:
        asyncio.run(main())
    except Exception:
        log.critical('Unhandled error occurred.', exc_info=True)
        sys.exit(1)
    except (SystemExit, KeyboardInterrupt):
        sys.exit(0)
    else:
        sys.exit(0)
