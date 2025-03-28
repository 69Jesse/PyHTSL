from ..expression import Expression
from ..condition import Condition, Operator, OperatorCondition, PlaceholderValue

from typing import TYPE_CHECKING, final
if TYPE_CHECKING:
    from typing import Self
    from .stat import Stat


__all__ = (
    'StatValue',
)


@final
class StatValue:
    stat: 'Stat'
    def __init__(
        self,
        stat: 'Stat',
    ) -> None:
        self.stat = stat

    def __iadd__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.iadd(self.stat, other)
        return self

    def __add__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.add(self.stat, other)

    def __radd__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.radd(other, self.stat)

    def __isub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.isub(self.stat, other)
        return self

    def __sub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.sub(self.stat, other)

    def __rsub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.rsub(other, self.stat)

    def set(self, value: 'Expression | Stat | int | PlaceholderValue') -> None:
        return Expression.set(self.stat, value)

    def __imul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.imul(self.stat, other)
        return self

    def __mul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.mul(self.stat, other)

    def __rmul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.rmul(other, self.stat)

    def __itruediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.itruediv(self.stat, other)
        return self

    def __truediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.truediv(self.stat, other)

    def __rtruediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.rtruediv(other, self.stat)

    def __ifloordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.ifloordiv(self.stat, other)
        return self

    def __floordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.floordiv(self.stat, other)

    def __rfloordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.rfloordiv(other, self.stat)

    def __ipow__(self, other: int) -> 'Self':
        Expression.ipow(self.stat, other)
        return self

    def __pow__(self, other: int) -> Expression | int:
        return Expression.pow(self.stat, other)

    def __imod__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.imod(self.stat, other)
        return self

    def __mod__(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.mod(self.stat, other)

    def safemod(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.safemod(self.stat, other)

    def unsafemod(self, other: 'Expression | Stat | int | PlaceholderValue') -> Expression:
        return Expression.unsafemod(self.stat, other)

    def __neg__(self) -> Expression:
        return Expression.neg(self.stat)

    def sign(self) -> Expression:
        return Expression.sign(self.stat)

    def __abs__(self) -> Expression:
        return Expression.abs(self.stat)

    def __eq__(self, other: 'Stat | PlaceholderValue | int') -> Condition:
        return OperatorCondition(self.stat, other, Operator.Equal)
