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

    def __iadd__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.iadd(self.stat, other)
        return self

    def __add__(self, other: 'Expression | Stat | int') -> Expression:
        return Expression.add(self.stat, other)

    def __radd__(self, other: 'Expression | Stat | int') -> Expression:
        return Expression.radd(self.stat, other)

    def __isub__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.isub(self.stat, other)
        return self

    def __sub__(self, other: 'Expression | Stat | int') -> Expression:
        return Expression.sub(self.stat, other)

    def __rsub__(self, other: 'Expression | Stat | int') -> Expression:
        return Expression.rsub(self.stat, other)

    def set(self, value: 'Expression | Stat | int') -> None:
        return Expression.set(self.stat, value)

    def __imul__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.imul(self.stat, other)
        return self

    def __mul__(self, other: 'Expression | Stat | int') -> Expression:
        return Expression.mul(self.stat, other)

    def __rmul__(self, other: 'Expression | Stat | int') -> Expression:
        return Expression.rmul(self.stat, other)

    def __itruediv__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.itruediv(self.stat, other)
        return self

    def __truediv__(self, other: 'Expression | Stat | int') -> Expression:
        return Expression.truediv(self.stat, other)

    def __ifloordiv__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.ifloordiv(self.stat, other)
        return self

    def __floordiv__(self, other: 'Expression | Stat | int') -> Expression:
        return Expression.floordiv(self.stat, other)

    def __neg__(self) -> Expression:
        return Expression.neg(self.stat)

    def __eq__(self, other: 'Stat | PlaceholderValue | int') -> Condition:
        return OperatorCondition(self.stat, other, Operator.Equal)
