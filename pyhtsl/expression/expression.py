from abc import abstractmethod
from typing import Self

from ..base_object import BaseObject


__all__ = ('Expression',)


class Expression(BaseObject):
    @abstractmethod
    def into_htsl(self) -> str:
        raise NotImplementedError()

    def execute(self) -> Self:
        # TODO write htsl
        return self
