from .writer import WRITER, LineType
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

    def __iadd__(self, other: Checkable | NumericHousingType) -> Self:
        expr = Expression(self, self._other_as_type_compatible(other), ExpressionOperator.Increment)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()
        return self

    def __isub__(self, other: Checkable | NumericHousingType) -> Self:
        expr = Expression(self, self._other_as_type_compatible(other), ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()
        return self

    def __imul__(self, other: Checkable | NumericHousingType) -> Self:
        expr = Expression(self, self._other_as_type_compatible(other), ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()
        return self

    def __itruediv__(self, other: Checkable | NumericHousingType) -> Self:
        expr = Expression(self, self._other_as_type_compatible(other), ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()
        return self

    def __ifloordiv__(self, other: Checkable | NumericHousingType) -> Self:
        return self.__itruediv__(other)

    def __ipow__(self, other: int) -> Self:
        self.set(self.__pow__(self._other_as_type_compatible(other)))  # type: ignore
        return self

    def __imod__(self, other: Checkable | NumericHousingType) -> Self:
        self.set(self.__mod__(self._other_as_type_compatible(other)))  # type: ignore
        return self

    def set(self, right: Checkable | HousingType) -> Self:
        expr = Expression(self, self._other_as_type_compatible(right), ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()
        return self

    def unset(self) -> None:
        WRITER.write(
            f'{self._in_assignment_left_side()} unset', 
            LineType.variable_change,
        )

    def inc(self, other: Checkable | NumericHousingType) -> Self:
        return self.__iadd__(other)

    def dec(self, other: Checkable | NumericHousingType) -> Self:
        return self.__isub__(other)

    def mul(self, other: Checkable | NumericHousingType) -> Self:
        return self.__imul__(other)

    def div(self, other: Checkable | NumericHousingType) -> Self:
        return self.__itruediv__(other)

    def execute(self, operator: 'ExpressionOperator', other: Checkable | HousingType) -> Self:
        if operator is ExpressionOperator.Set:
            return self.set(other)
        elif operator is ExpressionOperator.Increment:
            return self.inc(other)  # type: ignore
        elif operator is ExpressionOperator.Decrement:
            return self.dec(other)  # type: ignore
        elif operator is ExpressionOperator.Multiply:
            return self.mul(other)  # type: ignore
        elif operator is ExpressionOperator.Divide:
            return self.div(other)  # type: ignore
        else:
            raise ValueError(f'Unknown operator {operator}')

    @property
    def value(self) -> Self:
        return self

    @value.setter
    def value(self, value: Checkable | HousingType) -> None:
        self.set(value)

    def with_value(self, value: Checkable | HousingType) -> Self:
        self.set(value)
        return self
