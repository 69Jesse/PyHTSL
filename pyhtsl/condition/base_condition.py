from abc import ABC, abstractmethod


__all__ = ('BaseCondition',)


class BaseCondition(ABC):
    inverted: bool = False
    __slots__ = ()

    @abstractmethod
    def create_line(self) -> str:
        raise NotImplementedError

    def __invert__(self) -> 'BaseCondition':
        self.inverted = not self.inverted
        return self

    def __str__(self) -> str:
        return ('!' * self.inverted) + self.create_line()
