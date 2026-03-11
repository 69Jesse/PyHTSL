from typing import Self

from .condition import Condition

__all__ = ('NamedCondition',)


class NamedCondition(Condition):
    name: str

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    def into_htsl_raw(self) -> str:
        return self.name

    def cloned_raw(self) -> Self:
        return self.__class__(
            name=self.name,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, NamedCondition):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name} inverted={self.inverted}>'
