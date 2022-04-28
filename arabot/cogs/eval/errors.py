import re
import traceback
from collections.abc import Sequence

from .abc import Evaluator

__all__ = [
    "EvalException",
    "LocalEvalCompileException",
    "LocalEvalExecuteException",
    "LocalEvalException",
    "RemoteEvalException",
    "RemoteEvalBadResponse",
]


class EvalException(Exception):
    pass


class LocalEvalException(EvalException):
    def __init__(self, error: BaseException):
        self.original = error

    def format(self, *, source: str | Sequence = "", filename: str = Evaluator.TB_FILENAME) -> str:
        if isinstance(source, str):
            source = source.strip().splitlines()

        # tb_header = "Traceback (most recent call last):\n"
        # tb_frames = traceback.extract_tb(self.original.__traceback__)
        # tb_repl_frames = []
        # for frame in tb_frames:
        #     if frame.filename != filename:
        #         continue
        #     if sourcelines:
        #         frame._line = sourcelines[frame.lineno - 1]
        #     tb_repl_frames.append(frame)
        # tb_repl_frames = traceback.format_list(tb_repl_frames)
        # exc_msg = traceback.format_exception_only(self.original)
        # tb_formatted = tb_header + "".join(tb_repl_frames + exc_msg)

        tb = traceback.TracebackException.from_exception(self.original)
        tb_repl_frames = []
        for frame in tb.stack:
            if frame.filename != filename:
                continue
            if source:
                frame._line = source[frame.lineno - 1]
            tb_repl_frames.append(frame)
        tb.stack = traceback.StackSummary.from_list(tb_repl_frames)
        tb_formatted = "".join(tb.format(chain=False))

        return tb_formatted


class LocalEvalCompileException(LocalEvalException):
    pass


class LocalEvalExecuteException(LocalEvalException):
    def __init__(self, error: BaseException, output_before_error: str = ""):
        super().__init__(error)
        self.stdout = output_before_error


class RemoteEvalException(EvalException):
    def __init__(self, error: str, output_before_error: str = "", exit_code: int = 1):
        self.error = error
        self.stdout = output_before_error
        self.exit_code = exit_code

    def format(self, *, filename: str = Evaluator.TB_FILENAME) -> str:
        tb_formatted = re.sub(
            r'(?<=^ {2}File ")/piston/jobs/[a-f\d]{8}(?:-[a-f\d]{4}){3}-[a-f\d]{12}/[^/]+?(?=")',
            filename,
            self.error,
            flags=re.ASCII | re.MULTILINE,
        )
        return tb_formatted


class RemoteEvalBadResponse(Exception):
    def __init__(self, message: str):
        self.message = message
