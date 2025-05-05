from .expression.handler import EXPR_HANDLER
from .checkable import Checkable
from .expression.housing_type import NumericHousingType, HousingType

from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from .expression.assignment_expression import Expression, ExpressionOperator


__all__ = (
    'Editable',
)


class Editable(Checkable):
    @staticmethod
    def _import_expression(
        expression_cls: type['Expression'],
        expression_operator_cls: type['ExpressionOperator'],
    ) -> None:
        globals()[expression_cls.__name__] = expression_cls
        globals()[expression_operator_cls.__name__] = expression_operator_cls

    @staticmethod
    def iadd(
        left: 'Editable',
        right: 'Checkable | NumericHousingType',
    ) -> None:
        expr = Expression(left, right, ExpressionOperator.Increment)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    def __iadd__(self, other: 'Checkable | NumericHousingType') -> 'Self':
        Editable.iadd(self, other)
        return self

    @staticmethod
    def isub(
        left: 'Editable',
        right: 'Checkable | NumericHousingType',
    ) -> None:
        expr = Expression(left, right, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    def __isub__(self, other: 'Checkable | NumericHousingType') -> 'Self':
        Editable.isub(self, other)
        return self

    @staticmethod
    def imul(
        left: 'Editable',
        right: 'Checkable | NumericHousingType',
    ) -> None:
        expr = Expression(left, right, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    def __imul__(self, other: 'Checkable | NumericHousingType') -> 'Self':
        Editable.imul(self, other)
        return self

    @staticmethod
    def itruediv(
        left: 'Editable',
        right: 'Checkable | NumericHousingType',
    ) -> None:
        expr = Expression(left, right, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    def __itruediv__(self, other: 'Checkable | NumericHousingType') -> 'Self':
        Editable.itruediv(self, other)
        return self

    @staticmethod
    def ifloordiv(
        left: 'Editable',
        right: 'Checkable | NumericHousingType',
    ) -> None:
        return Editable.itruediv(left, right)

    def __ifloordiv__(self, other: 'Checkable | NumericHousingType') -> 'Self':
        Editable.ifloordiv(self, other)
        return self

    @staticmethod
    def ipow(
        left: 'Editable',
        right: int,
    ) -> None:
        return Editable.set(left, Checkable.pow(left, right))

    def __ipow__(self, other: int) -> 'Self':
        Editable.ipow(self, other)
        return self

    @staticmethod
    def imod(
        left: 'Editable',
        right: 'Checkable | NumericHousingType',
    ) -> None:
        Editable.set(left, Checkable.mod(left, right))

    def __imod__(self, other: 'Checkable | NumericHousingType') -> 'Self':
        Editable.imod(self, other)
        return self

    @staticmethod
    def set(
        left: 'Editable',
        right: 'Checkable | HousingType',
    ) -> None:
        expr = Expression(left, right, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    @property
    def value(self) -> Self:
        return self

    @value.setter
    def value(self, value: 'Checkable | HousingType') -> None:
        return Editable.set(self, value)

    def with_value(
        self,
        value: 'Checkable | HousingType',
    ) -> Self:
        self.value = value
        return self
