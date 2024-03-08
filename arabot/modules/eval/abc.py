from abc import abstractmethod
from typing import Any, Protocol


class Evaluator(Protocol):
    TB_FILENAME = "<repl>"

    @abstractmethod
    async def run(self, code: str, *args, **kwargs) -> tuple[str, Any]: ...
