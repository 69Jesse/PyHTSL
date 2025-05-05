from ..stats.stat_parameter import StatParameter

from typing import Optional


__all__ = (
    'Function',
)


class Function:
    name: str
    parameters: list[StatParameter]
    def __init__(
        self,
        name: str,
        parameters: Optional[list[StatParameter]] = None,
    ) -> None:
        self.name = name
        self.parameters = parameters or []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Function):
            return NotImplemented
        return self.name == other.name and self.parameters == other.parameters
