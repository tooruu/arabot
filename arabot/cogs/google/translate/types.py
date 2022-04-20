from typing import TypeVar

Detection = TypeVar("Detection", bound=dict[str, str | bool | float])
LangCodeAndOrName = list[str]
