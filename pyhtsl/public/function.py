from ..stat import StatParameter

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
