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
    ) -> None:
        self.__add__(other).write()

    def __isub__(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        self.__sub__(other).write()

    def __imul__(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        self.__mul__(other).write()

    def __itruediv__(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        self.__truediv__(other).write()

    def __ifloordiv__(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        self.__floordiv__(other).write()

    def __ipow__(self, other: int) -> None:
        result = self.__pow__(other)
        if isinstance(result, Expression):
            result.write()

    def __imod__(self, other: Checkable | NumericHousingType) -> None:
        self.__mod__(other).write()

    def __iand__(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        self.__and__(other).write()

    def __ior__(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        self.__or__(other).write()

    def __ixor__(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        self.__xor__(other).write()

    def __ilshift__(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        self.__lshift__(other).write()

    def __irshift__(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        self.__rshift__(other).write()

    def set(
        self,
        value: Checkable | HousingType,
        *,
        allow_self_assignment: bool = False,
    ) -> None:
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        BinaryExpression(
            left=self,
            right=value,
            operator=BinaryOperator.Set,
            allow_self_assignment=allow_self_assignment,
        ).write()

    def inc(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        return self.__iadd__(other)

    def dec(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        return self.__isub__(other)

    def mul(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        return self.__imul__(other)

    def div(
        self,
        other: Checkable | NumericHousingType,
    ) -> None:
        return self.__itruediv__(other)

    def write(
        self,
        operator: 'BinaryOperator',
        other: Checkable | HousingType,
    ) -> None:
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
        if value is None:
            # `x.value += 1` gets replaced with `x.value = x.value.__iadd__(1)`, `x.value.__iadd__(1)` returns `None`
            return
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
