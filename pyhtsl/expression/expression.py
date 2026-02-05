from abc import abstractmethod

from ..base_object import BaseObject


__all__ = ('Expression',)


class Expression(BaseObject):
    @abstractmethod
    def into_htsl(self) -> str:
        raise NotImplementedError()
