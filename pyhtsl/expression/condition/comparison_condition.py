from .base_condition import BaseCondition

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
class ComparisonCondition(BaseCondition):
    left: 'Checkable'
    right: 'Checkable | HousingType'
    operator: ComparisonOperator

    def __init__(
        self,
        left: 'Checkable',
        right: 'Checkable | HousingType',
        operator: ComparisonOperator,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator

    def into_htsl_raw(self) -> str:
        line = f'{self.left._in_comparison_left_side()} {self.operator.value} {Checkable._to_comparison_right_side(self.right)}'
        fallback_value = self.left._get_formatted_fallback_value()
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
