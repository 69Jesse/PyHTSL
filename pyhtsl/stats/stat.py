from abc import abstractmethod

from ..expression.housing_type import HousingType
from ..expression.unset_expression import UnsetExpression
from ..internal_type import InternalType
from ..public.no_fallback_values import no_fallback_values
from ..editable import Editable

from typing import Self


__all__ = ('Stat',)


class Stat(Editable):
    name: str
    auto_unset: bool

    def __init__(
        self,
        name: str,
        /,
        *,
        internal_type: InternalType = InternalType.ANY,
        fallback_value: HousingType | None = None,
        auto_unset: bool = True,
    ) -> None:
        super().__init__(
            internal_type=internal_type,
            fallback_value=fallback_value,
        )
        self.name = name
        self.auto_unset = auto_unset

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

    def into_assignment_left_side(self) -> str:
        return f'{self._left_side_keyword()} "{self.name}"'

    def into_assignment_right_side(self, *, include_internal_type: bool = True) -> str:
        name = self.into_string()
        return self._formatted_with_internal_type(
            name, include_internal_type=include_internal_type
        )

    def into_comparison_left_side(self) -> str:
        return self.into_assignment_left_side()

    def into_comparison_right_side(self) -> str:
        return self.into_assignment_right_side()

    def _as_string_first(self) -> str:
        return f'%var.{self._right_side_keyword()}/{self.name}'

    def _as_string_second(self, include_fallback_value: bool = True) -> str:
        if not include_fallback_value or no_fallback_values():
            return ''
        fallback_value = self.get_formatted_fallback_value()

        if (
            isinstance(fallback_value, str)
            and not fallback_value
            or fallback_value == '""'
        ):
            return ''
        if (
            isinstance(fallback_value, str)
            and ' ' in fallback_value
            and not (fallback_value.startswith('"') and fallback_value.endswith('"'))
        ):
            raise ValueError(
                "Fallback values cannot have spaces inside of them because of HTSL's limitations.. Wrap them in double quotes yourself."
            )

        if fallback_value is None:
            return ''
        return f' {fallback_value}'

    def _as_string_third(self) -> str:
        return '%'

    def into_string(self, include_fallback_value: bool = True) -> str:
        return (
            self._as_string_first()
            + self._as_string_second(include_fallback_value=include_fallback_value)
            + self._as_string_third()
        )

    def equals_raw(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.name == other.name

    def is_same_stat(self, other: 'Stat') -> bool:
        return self.equals_raw(other)

    def with_automatic_unset(self) -> Self:
        """
        Creates a copy of the current object, with the automatic unset flag set to True.
        """
        clone = self.cloned()
        clone.auto_unset = True
        return clone

    def without_automatic_unset(self) -> Self:
        """
        Creates a copy of the current object, with the automatic unset flag set to False.
        """
        clone = self.cloned()
        clone.auto_unset = False
        return clone

    def cloned(self) -> Self:
        clone = super().cloned()
        clone.auto_unset = self.auto_unset
        return clone

    def unset(self) -> UnsetExpression:
        return UnsetExpression(self).execute()
