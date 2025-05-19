from abc import abstractmethod

from ..editable import Editable

from typing import TYPE_CHECKING


__all__ = (
    'BaseStat',
)


class BaseStat(Editable):
    name: str
    if TYPE_CHECKING:
        def __init__(self, name: str, /) -> None:
            ...
    else:
        def __init__(
            self,
            name: str,
            /,
            *,
            set_name: bool = True,
        ) -> None:
            if set_name:
                self.name = name

    def __hash__(self) -> int:
        return hash((self.__class__, self.name))

    @staticmethod
    @abstractmethod
    def _left_side_keyword() -> str:
        """
        var foo = %var.player/bar%
        ^^^
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _right_side_keyword() -> str:
        """
        var foo = %var.player/bar%
                       ^^^^^^
        """
        raise NotImplementedError

    def _in_assignment_left_side(self) -> str:
        return f'{self._left_side_keyword()} {self.name}'

    def _in_assignment_right_side(self) -> str:
        name = f'%var.{self._right_side_keyword()}/{self.name}'
        fallback_value = self._get_formatted_fallback_value()
        if fallback_value is not None:
            name += f' {fallback_value}'
        name += '%'
        return name

    def _in_comparison_left_side(self) -> str:
        return self._in_assignment_left_side()

    def _in_comparison_right_side(self) -> str:
        return self._in_assignment_right_side()

    def _as_string(self) -> str:
        return f'%var.{self._right_side_keyword()}/{self.name}%'
