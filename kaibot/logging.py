import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
from urllib.parse import quote

from rich.console import Console
from rich.style import Style
from rich.theme import Theme
from rich._log_render import LogRender
from rich.table import Table
from rich.text import Text
from rich.containers import Renderables
from rich.logging import RichHandler
from rich.traceback import Traceback


class CustomLogRender(LogRender):
    def __call__(
        self,
        console,
        renderables,
        log_time=None,
        time_format=None,
        level='',
        path=None,
        line_no=None,
        link_path=None,
        logger_name=None,
    ):
        output = Table.grid(padding=(0, 1))
        output.expand = True
        if self.show_time:
            output.add_column(style='log.time')
        if self.show_level:
            output.add_column(style='log.level', width=self.level_width)
        output.add_column(ratio=1, style='log.message', overflow='fold')
        if logger_name:
            output.add_column(style='log.path')
        if self.show_path and path:
            output.add_column(style='log.path')
        row = []
        if self.show_time:
            log_time = log_time or console.get_datetime()
            log_time_display = log_time.strftime(time_format or self.time_format)
            if log_time_display == self._last_time:
                row.append(Text(' ' * len(log_time_display)))
            else:
                row.append(Text(log_time_display))
                self._last_time = log_time_display
        if self.show_level:
            row.append(level)

        row.append(Renderables(renderables))

        hyperlink_style = f'link file://{quote(link_path)}' if link_path else ''
        if logger_name:
            logger_name_text = Text.from_markup(f'[[{hyperlink_style}]{logger_name}[/]]')
            row.append(logger_name_text)
        if self.show_path and path:
            path_text = Text(path, style=hyperlink_style)
            if line_no:
                path_text.append(f':{line_no}')
            row.append(path_text)

        output.add_row(*row)
        return output


class CustomRichHandler(RichHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_render = CustomLogRender(
            show_time=self._log_render.show_time,
            show_level=self._log_render.show_level,
            show_path=self._log_render.show_path,
            level_width=self._log_render.level_width,
        )

    def get_level_text(self, record) -> Text:
        """Get the level name from the record.

        Args:
            record (LogRecord): LogRecord instance.

        Returns:
            Text: A tuple of the style and level name.
        """
        level_name = record.levelname
        level_text = Text.styled(level_name.ljust(8), f'logging.level.{level_name.lower()}')
        return level_text

    def emit(self, record) -> None:
        """Invoked by logging."""
        path = Path(record.pathname).name
        level = self.get_level_text(record)
        message = self.format(record)
        time_format = None if self.formatter is None else self.formatter.datefmt
        log_time = datetime.fromtimestamp(record.created)

        traceback = None
        if self.rich_tracebacks and record.exc_info and record.exc_info != (None, None, None):
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None
            traceback = Traceback.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                width=self.tracebacks_width,
                extra_lines=self.tracebacks_extra_lines,
                theme=self.tracebacks_theme,
                word_wrap=self.tracebacks_word_wrap,
                show_locals=self.tracebacks_show_locals,
                locals_max_length=self.locals_max_length,
                locals_max_string=self.locals_max_string,
            )
            message = record.getMessage()

        use_markup = getattr(record, 'markup') if hasattr(record, 'markup') else self.markup
        if use_markup:
            message_text = Text.from_markup(message)
        else:
            message_text = Text(message)

        if self.highlighter:
            message_text = self.highlighter(message_text)
        if self.KEYWORDS:
            message_text.highlight_words(self.KEYWORDS, 'logging.keyword')

        self.console.print(
            self._log_render(
                self.console,
                [message_text] if not traceback else [message_text, traceback],
                log_time=log_time,
                time_format=time_format,
                level=level,
                path=path,
                line_no=record.lineno,
                link_path=record.pathname if self.enable_link_path else None,
                logger_name=record.name,
            )
        )


def config_logging(levels: Dict[str, int] = None, location: Path = Path()):
    if levels is None:
        levels = {'file': logging.DEBUG, 'stdout': logging.INFO}

    bot_logger = logging.getLogger('kaibot')
    bot_logger.setLevel(levels['file'])
    dpy_logger = logging.getLogger('discord')
    dpy_logger.setLevel(logging.WARNING)

    file_formatter = logging.Formatter(
        '[{asctime}] [{levelname}] {name}: {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{',
    )

    theme = Theme(
        {
            'logging.level.warning': Style(color='yellow'),
            'logging.level.info': Style(color='bright_blue'),
        }
    )
    console = Console(theme=theme)
    rich_formatter = logging.Formatter(datefmt='[%X]')
    stdout_handler = CustomRichHandler(console=console, show_path=False, rich_tracebacks=True)
    stdout_handler.setFormatter(rich_formatter)

    stdout_handler.setLevel(levels['stdout'])

    bot_logger.addHandler(stdout_handler)

    if not location.exists():
        location.mkdir(parents=True, exist_ok=True)

    for logger in (bot_logger, dpy_logger):
        handler = logging.FileHandler(filename=f'{location.resolve() / logger.name}.log')
        handler.setFormatter(file_formatter)
        logger.addHandler(handler)
