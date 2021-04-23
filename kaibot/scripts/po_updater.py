import logging
import sys
from pathlib import Path

from babel.messages.frontend import update_catalog

log = logging.getLogger('kaibot.po_updater')


def initialize_options(updater: update_catalog, **options):
    updater.initialize_options()
    for key, value in options.items():
        setattr(updater, key, value)


def main(path: Path):
    pot_files = tuple(l for l in path.iterdir() if l.name.endswith('.pot'))

    if not pot_files:
        res = 1
        log.error('No pot files.')
    res = 0

    for file in pot_files:
        updater = update_catalog()
        initialize_options(
            updater,
            domain=file.name[:-4],
            input_file=file,
            output_dir=str(path),
            update_header_comment=True,
            log=log,
        )

        res = updater.run()

    return res


if __name__ == '__main__':
    handler = logging.StreamHandler()
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    sys.exit(main(Path('locales')))
