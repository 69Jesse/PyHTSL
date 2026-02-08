from abc import ABC, abstractmethod
from typing import Self


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
