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
        # Subclasses (PlayerSneaking, ...) hardcode their name with a no-arg
        # __init__, so reconstruct without calling it.
        clone = self.__class__.__new__(self.__class__)
        clone.name = self.name
        return clone

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, NamedCondition):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name} inverted={self.inverted}>'
