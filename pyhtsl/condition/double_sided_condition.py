from .base_condition import BaseCondition

from enum import Enum

from typing import TYPE_CHECKING, final
if TYPE_CHECKING:
    from ..checkable import Checkable
    from ..expression.housing_type import HousingType


__all__ = (
    'DoubleSidedConditionOperator',
    'DoubleSidedCondition',
)


class DoubleSidedConditionOperator(Enum):
    Equal = '=='
    GreaterThan = '>'
    LessThan = '<'
    GreaterThanOrEqual = '>='
    LessThanOrEqual = '<='


@final
class DoubleSidedCondition(BaseCondition):
    @staticmethod
    def _import_checkable(
        checkable_cls: type['Checkable'],
    ) -> None:
        globals()[checkable_cls.__name__] = checkable_cls

    left: 'Checkable'
    right: 'Checkable | HousingType'
    operator: DoubleSidedConditionOperator
    def __init__(
        self,
        left: 'Checkable',
        right: 'Checkable | HousingType',
        operator: DoubleSidedConditionOperator,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator

    def create_line(self) -> str:
        line = f'{self.left._in_comparison_left_side()} {self.operator.value} {Checkable._to_comparison_right_side(self.right)}'
        fallback_value = self.left._get_formatted_fallback_value()
        if fallback_value is not None:
            line += f' {fallback_value}'
        return line
