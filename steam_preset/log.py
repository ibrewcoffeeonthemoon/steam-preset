import logging
import os
import sys
from enum import Enum
from logging import Formatter, LogRecord, StreamHandler


class LogLevel(str, Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


# decode raw environment variable
def _get_color(env_var: str) -> str:
    raw_val = os.environ.get(env_var, '')
    return raw_val.encode('utf-8').decode('unicode_escape') if raw_val else ''


# logging formatter
class _EnvColorFormatter(Formatter):
    reset = _get_color('RESET')
    format_str = '%(name)s: %(levelname)s: %(message)s'
    colors = {
        logging.DEBUG: _get_color('BLUE'),
        logging.INFO: _get_color('GREEN'),
        logging.WARNING: _get_color('YELLOW'),
        logging.ERROR: _get_color('RED'),
        logging.CRITICAL: _get_color('RED'),
    }

    def format(self, record: LogRecord) -> str:
        color = self.colors.get(record.levelno, '')
        log_fmt = f'{color}{self.format_str}{self.reset}'
        formatter = Formatter(log_fmt)
        return formatter.format(record)


# setup logger with handler
_handler = StreamHandler(sys.stdout)
_handler.setFormatter(_EnvColorFormatter())
logger = logging.getLogger('steam-preset')
logger.setLevel(logging.INFO)
logger.addHandler(_handler)
