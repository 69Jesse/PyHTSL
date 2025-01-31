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

    def create_line(self) -> str:
        return self.name
