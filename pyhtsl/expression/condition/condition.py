from abc import abstractmethod

from ...base_object import BaseObject

from typing import Self, final


__all__ = ('Condition',)


class Condition(BaseObject):
    inverted: bool = False

    @abstractmethod
    def into_htsl_raw(self) -> str:
        raise NotImplementedError

    @final
    def into_htsl(self) -> str:
        return ('!' * self.inverted) + self.into_htsl_raw()

    @abstractmethod
    def equals_raw(self, other: object) -> bool:
        raise NotImplementedError

    @final
    def equals(self, other: object) -> bool:
        if not isinstance(other, Condition):
            return False
        return self.inverted == other.inverted and self.equals_raw(other)

    def __invert__(self) -> Self:
        self.inverted = not self.inverted
        return self
