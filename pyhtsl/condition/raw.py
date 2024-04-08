from .condition import Condition

from typing import final


__all__ = (
    'RawCondition',
)


@final
class RawCondition(Condition):
    name: str
    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name
