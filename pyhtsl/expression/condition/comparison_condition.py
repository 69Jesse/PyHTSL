from expression.housing_type import housing_type_as_right_side
from .condition import Condition

from enum import Enum

from typing import TYPE_CHECKING, Self, final

if TYPE_CHECKING:
    from ...checkable import Checkable
    from ...expression.housing_type import HousingType


__all__ = (
    'ComparisonOperator',
    'ComparisonCondition',
)


class ComparisonOperator(Enum):
    Equal = '=='
    GreaterThan = '>'
    LessThan = '<'
    GreaterThanOrEqual = '>='
    LessThanOrEqual = '<='


@final
class ComparisonCondition[LeftT: 'Checkable', RightT: 'Checkable | HousingType'](
    Condition
):
    left: LeftT
    right: RightT
    operator: ComparisonOperator

    def __init__(
        self,
        left: LeftT,
        right: RightT,
        operator: ComparisonOperator,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator

    def into_htsl_raw(self) -> str:
        def format_rhs(value: Checkable | HousingType) -> str:
            if isinstance(value, Checkable):
                return value.into_comparison_right_side()
            return housing_type_as_right_side(value)

        line = f'{self.left.into_comparison_left_side()} {self.operator.value} {format_rhs(self.right)}'

        fallback_value = self.left.get_formatted_fallback_value()
        if fallback_value is not None:
            line += f' {fallback_value}'

        return line

    def cloned(self) -> Self:
        return self.__class__(
            left=self.left.cloned(),
            right=self.right.cloned()
            if isinstance(self.right, Checkable)
            else self.right,
            operator=self.operator,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, ComparisonCondition):
            return False
        return (
            self.left.equals(other.left)
            and (
                (
                    isinstance(self.right, Checkable)
                    and isinstance(other.right, Checkable)
                    and self.right.equals(other.right)
                )
                or (
                    not isinstance(self.right, Checkable)
                    and not isinstance(other.right, Checkable)
                    and self.right == other.right
                )
            )
            and self.operator == other.operator
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{repr(self.left)} {self.operator.value} {repr(self.right)}>'
