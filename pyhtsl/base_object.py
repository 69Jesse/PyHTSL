from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

from .expression.housing_type import housing_type_as_rhs

if TYPE_CHECKING:
    from .checkable import Checkable
    from .expression.housing_type import HousingType


class BaseObject(ABC):
    @abstractmethod
    def cloned(self) -> Self:
        raise NotImplementedError()

    @staticmethod
    def cloned_or_same[T: object](value: T) -> T:
        if isinstance(value, BaseObject):
            return value.cloned()
        return value

    @abstractmethod
    def equals(self, other: object) -> bool:
        raise NotImplementedError()

    @staticmethod
    def equals_or_eq(a: object, b: object) -> bool:
        if isinstance(a, BaseObject) and isinstance(b, BaseObject):
            return a.equals(b)
        if not isinstance(a, BaseObject) and not isinstance(b, BaseObject):
            return a == b
        return False

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError()

    def inline(self, value: 'Checkable | HousingType | bool') -> str:
        from .checkable import Checkable

        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, Checkable):
            return str(value)
        return housing_type_as_rhs(value)
