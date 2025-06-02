from ..stats.stat_parameter import StatParameter

from typing import Callable


__all__ = (
    'Function',
)


class Function:
    name: str
    parameters: list[StatParameter]
    callback: Callable[[], None] | None = None
    def __init__(
        self,
        name: str,
        parameters: list[StatParameter] | None = None,
        *,
        callback: Callable[[], None] | None = None,
    ) -> None:
        self.name = name
        self.parameters = parameters or []
        self.callback = callback

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Function):
            return NotImplemented
        return self.name == other.name and self.parameters == other.parameters
