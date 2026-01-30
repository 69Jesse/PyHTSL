from .writer import WRITER, LineType
from .expression.handler import EXPR_HANDLER
from .checkable import Checkable
from .expression.housing_type import NumericHousingType, HousingType

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from .expression.binary_expression import BinaryExpression, BinaryExpressionOperator


__all__ = ('Editable',)


class Editable(Checkable):
    @staticmethod
    def _import_binary_expression(
        binary_expression_cls: type['BinaryExpression'],
        binary_operator_cls: type['BinaryExpressionOperator'],
    ) -> None:
        globals()[binary_expression_cls.__name__] = binary_expression_cls
        globals()[binary_operator_cls.__name__] = binary_operator_cls

    def __iadd__(self, other: Checkable | NumericHousingType) -> Self:
        expr = BinaryExpression(
            self,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Increment,
        )
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()
        return self

    def __isub__(self, other: Checkable | NumericHousingType) -> Self:
        expr = BinaryExpression(
            self,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Decrement,
        )
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()
        return self

    def __imul__(self, other: Checkable | NumericHousingType) -> Self:
        expr = BinaryExpression(
            self,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Multiply,
        )
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()
        return self

    def __itruediv__(self, other: Checkable | NumericHousingType) -> Self:
        expr = BinaryExpression(
            self, self._other_as_type_compatible(other), BinaryExpressionOperator.Divide
        )
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()
        return self

    def __ifloordiv__(self, other: Checkable | NumericHousingType) -> Self:
        return self.__itruediv__(other)

    def __ipow__(self, other: int) -> Self:
        self.set(self.__pow__(other))  # type: ignore
        return self

    def __imod__(self, other: Checkable | NumericHousingType) -> Self:
        self.set(self.__mod__(other))
        return self

    def set(
        self, right: Checkable | HousingType, *, is_self_cast: bool = False
    ) -> Self:
        if is_self_cast and not self.equals(right, check_internal_type=False):
            raise ValueError('is_self_cast can only be True if lhs is equal to rhs')
        expr = BinaryExpression(
            self,
            self._other_as_type_compatible(right),
            BinaryExpressionOperator.Set,
            is_self_cast=is_self_cast,
        )
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

    def execute(
        self, operator: 'BinaryExpressionOperator', other: Checkable | HousingType
    ) -> Self:
        if operator is BinaryExpressionOperator.Set:
            return self.set(other)
        elif operator is BinaryExpressionOperator.Increment:
            return self.inc(other)  # type: ignore
        elif operator is BinaryExpressionOperator.Decrement:
            return self.dec(other)  # type: ignore
        elif operator is BinaryExpressionOperator.Multiply:
            return self.mul(other)  # type: ignore
        elif operator is BinaryExpressionOperator.Divide:
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

    def cast_to_long(self) -> Self:
        return self.set(self.as_long(), is_self_cast=True)

    def cast_to_double(self) -> Self:
        return self.set(self.as_double(), is_self_cast=True)

    def cast_to_string(self) -> Self:
        return self.set(self.as_string(), is_self_cast=True)
