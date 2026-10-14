import logging
import sys


def setup_logging(level: int) -> None:
    handlers = [StderrHandler()]
    if level < logging.WARNING:
        handlers.append(StdoutHandler(level))

    logging.basicConfig(
        format="%(asctime)s|%(name)s|%(levelname)s|%(message)s",
        level=logging.NOTSET,
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        handlers=handlers,
    )


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
            lambda record: (
                record.msg != 'We are being rate limited. Retrying in %.2f seconds. Handled under the bucket "%s"'
            )
        )
