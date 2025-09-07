from abc import abstractmethod

from ..public.no_fallback_values import no_fallback_values
from ..checkable import Checkable
from ..editable import Editable
from ..expression.handler import ExpressionHandler

from typing import TYPE_CHECKING, Self


__all__ = (
    'BaseStat',
)


class BaseStat(Editable):
    name: str
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
        return f'{self._left_side_keyword()} "{self.name}"'

    def _in_assignment_right_side(self, *, include_internal_type: bool = True) -> str:
        name = self._as_string()
        return self._formatted_with_internal_type(name, include_internal_type=include_internal_type)

    def _in_comparison_left_side(self) -> str:
        return self._in_assignment_left_side()

    def _in_comparison_right_side(self) -> str:
        return self._in_assignment_right_side()

    def _as_string_first(self) -> str:
        return f'%var.{self._right_side_keyword()}/{self.name}'

    def _as_string_second(self, include_fallback_value: bool = True) -> str:
        if not include_fallback_value or no_fallback_values():
            return ''
        fallback_value = self._get_formatted_fallback_value()

        if isinstance(fallback_value, str) and not fallback_value or fallback_value == '""':
            return ''
        if isinstance(fallback_value, str) and ' ' in fallback_value and not (fallback_value.startswith('"') and fallback_value.endswith('"')):
            raise ValueError('Fallback values cannot have spaces inside of them because of HTSL\'s limitations.. Wrap them in double quotes yourself.')

        if fallback_value is None:
            return ''
        return f' {fallback_value}'

    def _as_string_third(self) -> str:
        return '%'

    def _as_string(self, include_fallback_value: bool = True) -> str:
        return (
            self._as_string_first()
            + self._as_string_second(include_fallback_value=include_fallback_value)
            + self._as_string_third()
        )

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
        copied.unset = self.unset
        return copied

    def cast_to_long(self) -> Self:
        return self.set(self.as_long(), is_self_cast=True)

    def cast_to_double(self) -> Self:
        return self.set(self.as_double(), is_self_cast=True)

    def cast_to_string(self) -> Self:
        return self.set(self.as_string(), is_self_cast=True)


Checkable._import_base_stat(BaseStat)
ExpressionHandler._import_base_stat(BaseStat)
