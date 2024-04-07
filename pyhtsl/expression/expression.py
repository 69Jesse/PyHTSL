import os

from .handler import EXPR_HANDLER
from .expression_type import ExpressionType

from typing import TYPE_CHECKING, Optional, overload
if TYPE_CHECKING:
    from typing import Self
    from ..stat import Stat


__all__ = (
    'Expression',
)


class Expression:
    left: 'Expression | Stat'
    right: 'Expression | Stat | int'
    type: ExpressionType
    id: str
    def __init__(
        self,
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
        type: ExpressionType,
        id: Optional[str] = None,
    ) -> None:
        self.left = left
        self.right = right
        self.type = type
        self.id = id or os.urandom(8).hex()

    @overload
    def fetch_stat_or_int(self, maybe_stat: 'Expression | Stat') -> 'Stat':
        ...

    @overload
    def fetch_stat_or_int(self, maybe_stat: int) -> int:
        ...

    @overload
    def fetch_stat_or_int(self, maybe_stat: 'Expression | Stat | int') -> 'Stat | int':
        ...

    def fetch_stat_or_int(self, maybe_stat: 'Expression | Stat | int') -> 'Stat | int':
        while isinstance(maybe_stat, Expression):
            maybe_stat = maybe_stat.left
        return maybe_stat

    @staticmethod
    def iadd(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Increment)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    def __iadd__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.iadd(self, other)
        return self

    @staticmethod
    def add(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionType.Increment)
        EXPR_HANDLER.add(expr)
        return expr

    def __add__(self, other: 'Expression | Stat | int') -> 'Expression':
        return Expression.add(self, other)

    @staticmethod
    def isub(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Decrement)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    def __isub__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.isub(self, other)
        return self

    @staticmethod
    def sub(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionType.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    def __sub__(self, other: 'Expression | Stat | int') -> 'Expression':
        return Expression.sub(self, other)

    @staticmethod
    def set(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    @staticmethod
    def imul(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Multiply)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    def __imul__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.imul(self, other)
        return self

    @staticmethod
    def mul(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionType.Multiply)
        EXPR_HANDLER.add(expr)
        return expr

    def __mul__(self, other: 'Expression | Stat | int') -> 'Expression':
        return Expression.mul(self, other)

    @staticmethod
    def itruediv(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Divide)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    def __itruediv__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.itruediv(self, other)
        return self

    @staticmethod
    def truediv(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionType.Divide)
        EXPR_HANDLER.add(expr)
        return expr

    def __truediv__(self, other: 'Expression | Stat | int') -> 'Expression':
        return Expression.truediv(self, other)

    @staticmethod
    def ifloordiv(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> None:
        return Expression.itruediv(left, right)

    def __ifloordiv__(self, other: 'Expression | Stat | int') -> 'Self':
        Expression.ifloordiv(self, other)
        return self

    @staticmethod
    def floordiv(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> 'Expression':
        return Expression.truediv(left, right)

    def __floordiv__(self, other: 'Expression | Stat | int') -> 'Expression':
        return Expression.truediv(self, other)

    @staticmethod
    def neg(value: 'Expression | Stat') -> 'Expression':
        return Expression.mul(value, -1)

    def __neg__(self) -> 'Expression':
        return Expression.neg(self)

    def __repr__(self) -> str:
        return f'{repr(self.fetch_stat_or_int(self.left))} {self.type.value} {self.fetch_stat_or_int(self.right)}'
