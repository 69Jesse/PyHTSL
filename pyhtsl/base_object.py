from abc import abstractmethod, ABC
from typing import Self


class BaseObject(ABC):
    @abstractmethod
    def cloned(self) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def equals(self, other: object) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError()
