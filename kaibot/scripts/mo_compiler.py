import logging
import sys
from pathlib import Path

from babel.messages.frontend import compile_catalog

log = logging.getLogger('kaibot.mo_compiler')


def initialize_options(compiler: compile_catalog, **options):
    compiler.initialize_options()
    for key, value in options.items():
        setattr(compiler, key, value)


def main(path: Path, log: logging.Logger = log):
    languages = tuple(l for l in path.iterdir() if not l.name.endswith('.pot'))

    res = 0

    for language in languages:
        compiler = compile_catalog()
        domains = tuple(d.name[:-3] for d in language.glob('**/LC_*/*.po'))

        if not domains:
            log.warning(f'No {language.name} catalogs to compile.')
            res = 1
            continue

        initialize_options(
            compiler,
            directory=str(path),
            domain=domains,
            locale=language.name,
            log=log,
        )

        res = compiler.run()

    if not languages:
        log.error('No language folders.')
        res = 1

    return res


if __name__ == '__main__':
    handler = logging.StreamHandler()
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    sys.exit(main(Path('locales')))
