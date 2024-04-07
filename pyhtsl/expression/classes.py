from enum import Enum
import os

from .handler import EXPR_HANDLER

from typing import TYPE_CHECKING, Optional, overload
if TYPE_CHECKING:
    from ..stat import Stat


__all__ = (
    'ExpressionType',
    'Expression',
)


class ExpressionType(Enum):
    Increment = '+='
    Decrement = '-='
    Set = '='
    Multiply = '*='
    Divide = '/='


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

    @staticmethod
    def isub(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Decrement)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

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

    @staticmethod
    def itruediv(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Divide)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

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

    @staticmethod
    def ifloordiv(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> None:
        return Expression.itruediv(left, right)

    @staticmethod
    def floordiv(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int',
    ) -> 'Expression':
        return Expression.truediv(left, right)

    @staticmethod
    def neg(value: 'Expression | Stat') -> 'Expression':
        return Expression.mul(value, -1)

    def __repr__(self) -> str:
        return f'{repr(self.fetch_stat_or_int(self.left))} {self.type.value} {self.fetch_stat_or_int(self.right)}'
