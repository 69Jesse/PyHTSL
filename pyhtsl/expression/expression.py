from abc import abstractmethod
from typing import Self

from ..container import get_current_container

from ..base_object import BaseObject


__all__ = ('Expression',)


class Expression(BaseObject):
    @abstractmethod
    def into_htsl(self) -> str:
        raise NotImplementedError()

    def execute(self) -> Self:
        get_current_container().expressions.append(self.cloned())
        return self
