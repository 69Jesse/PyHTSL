from typing import TYPE_CHECKING, Self

from .checkable import Checkable
from .expression.expression import Expression
from .expression.housing_type import HousingType, NumericHousingType

if TYPE_CHECKING:
    from .expression.binary_expression import BinaryOperator


__all__ = ('Editable',)


class Editable(Checkable):
    def __iadd__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__add__(other).write()
        return self

    def __isub__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__sub__(other).write()
        return self

    def __imul__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__mul__(other).write()
        return self

    def __itruediv__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__truediv__(other).write()
        return self

    def __ifloordiv__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__floordiv__(other).write()
        return self

    def __ipow__(self, other: int) -> Self:
        result = self.__pow__(other)
        if isinstance(result, Expression):
            result.write()
        return self

    def __imod__(self, other: Checkable | NumericHousingType) -> Self:
        self.__mod__(other).write()
        return self

    def __iand__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__and__(other).write()
        return self

    def __ior__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__or__(other).write()
        return self

    def __ixor__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__xor__(other).write()
        return self

    def __ilshift__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__lshift__(other).write()
        return self

    def __irshift__(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        self.__rshift__(other).write()
        return self

    def set(
        self,
        value: Checkable | HousingType,
        *,
        is_intentional_self_assignment: bool = False,
    ) -> Self:
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        BinaryExpression(
            left=self,
            right=value,
            operator=BinaryOperator.Set,
            is_intentional_self_assignment=is_intentional_self_assignment,
        ).write()
        return self

    def inc(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        return self.__iadd__(other)

    def dec(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        return self.__isub__(other)

    def mul(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        return self.__imul__(other)

    def div(
        self,
        other: Checkable | NumericHousingType,
    ) -> Self:
        return self.__itruediv__(other)

    def apply(
        self,
        operator: 'BinaryOperator',
        other: Checkable | HousingType,
    ) -> Self:
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
        if self is value:
            return  # `foo.value += 123` -> `foo.value = foo.value.__iadd__(123)` -> `foo.value = foo`
        self.set(value)

    def with_value(self, value: Checkable | HousingType) -> Self:
        self.set(value)
        return self

    def cast_to_long(self) -> None:
        self.set(self.as_long(), is_intentional_self_assignment=True)

    def cast_to_double(self) -> None:
        self.set(self.as_double(), is_intentional_self_assignment=True)

    def cast_to_string(self) -> None:
        self.set(self.as_string(), is_intentional_self_assignment=True)
