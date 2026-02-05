from abc import abstractmethod

from ...base_object import BaseObject

from typing import final


__all__ = ('BaseCondition',)


class BaseCondition(BaseObject):
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
        if not isinstance(other, BaseCondition):
            return False
        return self.inverted == other.inverted and self.equals_raw(other)

    def __invert__(self) -> 'BaseCondition':
        self.inverted = not self.inverted
        return self
