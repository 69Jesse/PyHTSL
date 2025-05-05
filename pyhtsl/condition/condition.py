from .statements import IfStatement, ConditionalMode
from ..expression import Expression

from abc import ABC, abstractmethod
from enum import Enum

from typing import TYPE_CHECKING, final
if TYPE_CHECKING:
    from ..expression.checkable import Checkable
    from ..expression.housing_type import HousingType


__all__ = (
    'BaseCondition',
    'ConditionOperator',
    'DoubleSidedCondition',
)


class BaseCondition(ABC):
    inverted: bool = False
    __slots__ = ()

    @abstractmethod
    def create_line(self) -> str:
        raise NotImplementedError

    def __invert__(self) -> 'BaseCondition':
        self.inverted = not self.inverted
        return self

    def __str__(self) -> str:
        return ('!' * self.inverted) + self.create_line()


class ConditionOperator(Enum):
    Equal = '=='
    GreaterThan = '>'
    LessThan = '<'
    GreaterThanOrEqual = '>='
    LessThanOrEqual = '<='


@final
class DoubleSidedCondition(BaseCondition):
    left: 'Checkable'
    right: 'Checkable | HousingType'
    operator: ConditionOperator
    def __init__(
        self,
        left: 'Checkable',
        right: 'Checkable | HousingType',
        operator: ConditionOperator,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator

    def create_line(self) -> str:
        return f'{self.left.as_left_side()} {self.operator.value} {self.right.as_right_side()}'
