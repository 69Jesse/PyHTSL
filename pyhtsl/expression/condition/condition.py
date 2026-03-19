from abc import abstractmethod
from typing import TYPE_CHECKING, Self, final

from ...base_object import BaseObject

if TYPE_CHECKING:
    from ...checkable import Checkable
    from ...container import Container
    from ...execute.context import ExecutionContext
    from ...expression.housing_type import HousingType

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
    def cloned_raw(self) -> Self:
        raise NotImplementedError

    @final
    def cloned(self) -> Self:
        clone = self.cloned_raw()
        clone.inverted = self.inverted
        return clone

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

    def raw_evaluate(self, context: 'ExecutionContext') -> bool:
        print(f'No execution implemented for condition "{self!r}", returning False')
        return False

    @final
    def evaluate(self, context: 'ExecutionContext') -> bool:
        if context.verbose:
            print(f'Executing condition "{self!r}"')
        value = self.raw_evaluate(context)
        if self.inverted:
            value = not value
        return value

    def related_debug_parts(self) -> list['Checkable | HousingType']:
        return []

    def finalize(self, container: 'Container') -> None:
        self.into_htsl()
