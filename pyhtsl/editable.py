from typing import TYPE_CHECKING, Literal, Self

from .checkable import Checkable
from .expression.expression import Expression
from .expression.housing_type import HousingType, NumericHousingType

if TYPE_CHECKING:
    from .expression.binary_expression import BinaryExpression, BinaryOperator
    from .expression.compound_expression import CompoundExpression


__all__ = ('Editable',)


class Editable(Checkable):
    def __iadd__[T: Checkable | NumericHousingType](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        return self.__add__(other).write()

    def __isub__[T: Checkable | NumericHousingType](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        return self.__sub__(other).write()

    def __imul__[T: Checkable | NumericHousingType](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        return self.__mul__(other).write()

    def __itruediv__[T: Checkable | NumericHousingType](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        return self.__truediv__(other).write()

    def __ifloordiv__[T: Checkable | NumericHousingType](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        return self.__floordiv__(other).write()

    def __ipow__(self, other: int) -> 'CompoundExpression | Self | Literal[1]':
        result = self.__pow__(other)
        if isinstance(result, Expression):
            return result.write()
        return result

    def __imod__(self, other: Checkable | NumericHousingType) -> 'CompoundExpression':
        return self.__mod__(other).write()

    def set[T: Checkable | HousingType](
        self,
        value: T,
        *,
        allow_self_assignment: bool = False,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            left=self,
            right=value,
            operator=BinaryOperator.Set,
            allow_self_assignment=allow_self_assignment,
        ).write()

    def inc[T: Checkable | NumericHousingType](
        self, other: T
    ) -> 'BinaryExpression[Self, T]':
        return self.__iadd__(other)

    def dec[T: Checkable | NumericHousingType](
        self, other: T
    ) -> 'BinaryExpression[Self, T]':
        return self.__isub__(other)

    def mul[T: Checkable | NumericHousingType](
        self, other: T
    ) -> 'BinaryExpression[Self, T]':
        return self.__imul__(other)

    def div[T: Checkable | NumericHousingType](
        self, other: T
    ) -> 'BinaryExpression[Self, T]':
        return self.__itruediv__(other)

    def write[T: Checkable | HousingType](
        self,
        operator: 'BinaryOperator',
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryOperator

        if operator is BinaryOperator.Set:
            return self.set(other)

        if isinstance(other, HousingType) and not isinstance(other, NumericHousingType):
            raise ValueError(
                'Only numeric housing types can be used in increment/decrement/multiply/divide operations'
            )

        if operator is BinaryOperator.Increment:
            return self.inc(other)
        elif operator is BinaryOperator.Decrement:
            return self.dec(other)
        elif operator is BinaryOperator.Multiply:
            return self.mul(other)
        elif operator is BinaryOperator.Divide:
            return self.div(other)

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

    def cast_to_long(self) -> None:
        self.set(self.as_long(), allow_self_assignment=True)

    def cast_to_double(self) -> None:
        self.set(self.as_double(), allow_self_assignment=True)

    def cast_to_string(self) -> None:
        self.set(self.as_string(), allow_self_assignment=True)
