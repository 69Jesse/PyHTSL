from abc import abstractmethod

from ..checkable import Checkable
from ..editable import Editable
from ..expression.handler import ExpressionHandler

from typing import TYPE_CHECKING, Self


__all__ = (
    'BaseStat',
)


class BaseStat(Editable):
    name: str
    should_force_type_compatible: bool
    auto_unset: bool
    if TYPE_CHECKING:
        def __init__(
            self,
            name: str,
            /,
            *,
            unset: bool = True,
        ) -> None:
            ...
    else:
        def __init__(
            self,
            name: str,
            /,
            *,
            set_name: bool = True,
            unset: bool = True,
        ) -> None:
            if set_name:
                self.name = name
            self.should_force_type_compatible = True
            self.auto_unset = unset

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

    def _in_assignment_right_side(self, *, include_internal_type: bool = True) -> str:
        name = f'%var.{self._right_side_keyword()}/{self.name}'
        fallback_value = self._get_formatted_fallback_value()
        if fallback_value is not None:
            name += f' {fallback_value}'
        name += '%'
        return self._formatted_with_internal_type(name, include_internal_type=include_internal_type)

    def _in_comparison_left_side(self) -> str:
        return self._in_assignment_left_side()

    def _in_comparison_right_side(self) -> str:
        return self._in_assignment_right_side()

    def _as_string(self) -> str:
        return f'%var.{self._right_side_keyword()}/{self.name}%'

    def with_automatic_unset(self) -> Self:
        """
        Creates a copy of the current object, with the automatic unset flag set to True.
        """
        copied = self.copied()
        copied.auto_unset = True
        return copied

    def without_automatic_unset(self) -> Self:
        """
        Creates a copy of the current object, with the automatic unset flag set to False.
        """
        copied = self.copied()
        copied.auto_unset = False
        return copied

    def copied(self) -> Self:
        copied = super().copied()
        copied.should_force_type_compatible = self.should_force_type_compatible
        copied.unset = self.unset
        return copied


Checkable._import_base_stat(BaseStat)
ExpressionHandler._import_base_stat(BaseStat)
