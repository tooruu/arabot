import logging
import sys


class ThresholdFilter(logging.Filter):
    def __init__(self, min_level: int):
        super().__init__()
        self.min = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        return self.min <= record.levelno < logging.WARNING


class StdoutHandler(logging.StreamHandler):
    def __init__(self, min_level: int) -> None:
        super().__init__(sys.stdout)
        self.addFilter(ThresholdFilter(min_level))


class StderrHandler(logging.StreamHandler):
    def __init__(self) -> None:
        super().__init__(sys.stderr)
        self.setLevel(logging.WARNING)
        self.addFilter(
            lambda record: record.msg
            != 'We are being rate limited. Retrying in %.2f seconds. Handled under the bucket "%s"'
        )
