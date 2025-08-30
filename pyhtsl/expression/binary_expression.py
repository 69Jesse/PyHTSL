from ..checkable import Checkable
from ..editable import Editable
from .housing_type import HousingType
from .handler import ExpressionHandler
from .expression import Expression
from ..stats.base_stat import BaseStat
from ..line_type import LineType

from enum import Enum

from typing import final


__all__ = (
    'BinaryExpressionOperator',
    'BinaryExpression',
)


class BinaryExpressionOperator(Enum):
    Set = '='
    Increment = '+='
    Decrement = '-='
    Multiply = '*='
    Divide = '/='

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}, {self.value}>'


@final
class BinaryExpression(Expression):
    left: Editable
    right: Checkable | HousingType
    operator: BinaryExpressionOperator
    is_self_cast: bool

    def __init__(
        self,
        left: Editable,
        right: Checkable | HousingType,
        operator: BinaryExpressionOperator,
        is_self_cast: bool = False,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator
        self.is_self_cast = is_self_cast

    def _write_line(self) -> tuple[str, LineType]:
        line = f'{self.left._in_assignment_left_side()} {self.operator.value} {Checkable._to_assignment_right_side(self.right)}'
        if isinstance(self.left, BaseStat):
            line += f' {str(self.left.auto_unset).lower()}'
        if self.is_self_cast:
            line += '  // PyHTSL intended type cast'
        return line, LineType.variable_change

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{repr(self.left)} {self.operator.value} {repr(self.right)}>'


Checkable._import_binary_expression(BinaryExpression, BinaryExpressionOperator)
Editable._import_binary_expression(BinaryExpression, BinaryExpressionOperator)
ExpressionHandler._import_binary_expression(BinaryExpression, BinaryExpressionOperator)
