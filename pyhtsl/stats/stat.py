from abc import abstractmethod
from typing import Self

from ..actions.no_fallback_values import no_fallback_values
from ..editable import Editable
from ..expression.housing_type import HousingType
from ..expression.unset_expression import UnsetExpression
from ..internal_type import InternalType

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

    def into_hashable(self) -> tuple[object, ...]:
        return (*super().into_hashable(), self.name)

    @staticmethod
    @abstractmethod
    def left_side_keyword() -> str:
        """
        var foo = %var.player/bar%
        ^^^
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def right_side_keyword() -> str:
        """
        var foo = %var.player/bar%
                       ^^^^^^
        """
        raise NotImplementedError

    def into_string_lhs(self) -> str:
        return f'{self.left_side_keyword()} "{self.name}"'

    def into_string_rhs(self, *, include_internal_type: bool = True) -> str:
        name = self.into_inside_string()
        return self.format_with_internal_type(
            name,
            include_internal_type=include_internal_type,
        )

    def into_string_prefix(self) -> str:
        return f'%var.{self.right_side_keyword()}/{self.name}'

    def into_string_middle(self, include_fallback_value: bool = True) -> str:
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

    def into_string_suffix(self) -> str:
        return '%'

    def into_inside_string(self, include_fallback_value: bool = True) -> str:
        return (
            self.into_string_prefix()
            + self.into_string_middle(include_fallback_value=include_fallback_value)
            + self.into_string_suffix()
        )

    def equals_raw(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.name == other.name

    def is_same_stat(self, other: object) -> bool:
        return self.equals_raw(other)

    def with_auto_unset(self, flag: bool = True) -> Self:
        """
        Creates a copy of the current object, with the automatic unset flag set to the given value.
        """
        clone = self.cloned()
        clone.auto_unset = flag
        return clone

    def without_auto_unset(self) -> Self:
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

    def unset(self) -> None:
        UnsetExpression(self).write()
