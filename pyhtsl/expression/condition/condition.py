from abc import abstractmethod
from typing import TYPE_CHECKING, Self, final

from ...base_object import BaseObject

if TYPE_CHECKING:
    from ...execute.context import ExecutionContext

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

    def raw_execute(self, context: 'ExecutionContext') -> bool:
        print(f'No execution defined for condition "{self!r}", returning False')
        return False

    @final
    def execute(self, context: 'ExecutionContext') -> bool:
        if context.verbose:
            print(f'Executing condition "{self!r}"')
        value = self.raw_execute(context)
        if self.inverted:
            value = not value
        return value
