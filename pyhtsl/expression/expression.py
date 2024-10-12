import os

from .handler import EXPR_HANDLER
from .expression_type import ExpressionType

from typing import TYPE_CHECKING, Optional, overload
if TYPE_CHECKING:
    from typing import Self
    from ..stat import Stat
    from ..condition import PlaceholderValue, Condition, IfStatement
    PlaceholderValueCls = type['PlaceholderValue']


__all__ = (
    'Expression',
)


class Expression:
    _placeholder_value_cls: 'PlaceholderValueCls'

    left: 'Expression | Stat | PlaceholderValue'
    right: 'Expression | Stat | int | PlaceholderValue'
    type: ExpressionType
    id: str
    def __init__(
        self,
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
        type: ExpressionType,
        id: Optional[str] = None,
    ) -> None:
        self.left = left
        self.right = right
        self.type = type
        self.id = id or os.urandom(8).hex()

    @overload
    def fetch_stat_or_int(self, maybe_stat: 'Expression | Stat | PlaceholderValue') -> 'Stat | PlaceholderValue':
        ...

    @overload
    def fetch_stat_or_int(self, maybe_stat: int) -> int:
        ...

    @overload
    def fetch_stat_or_int(self, maybe_stat: 'Expression | Stat | int | PlaceholderValue') -> 'Stat | int | PlaceholderValue':
        ...

    def fetch_stat_or_int(self, maybe_stat: 'Expression | Stat | int | PlaceholderValue') -> 'Stat | int | PlaceholderValue':
        while isinstance(maybe_stat, Expression):
            maybe_stat = maybe_stat.left
        return maybe_stat

    @staticmethod
    def iadd(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Increment)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    @staticmethod
    def add(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionType.Increment)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def radd(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        return Expression.add(left, right)

    @staticmethod
    def isub(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Decrement)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    @staticmethod
    def sub(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionType.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def rsub(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, right, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.add(
            Expression(temp_stat, left, ExpressionType.Decrement),
        )
        return expr

    @staticmethod
    def set(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    @staticmethod
    def imul(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Multiply)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    @staticmethod
    def mul(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionType.Multiply)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def rmul(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        return Expression.mul(left, right)

    @staticmethod
    def itruediv(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> None:
        expr = Expression(left, right, ExpressionType.Divide)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.push()

    @staticmethod
    def truediv(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
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
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> None:
        return Expression.itruediv(left, right)

    @staticmethod
    def floordiv(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        return Expression.truediv(left, right)

    @staticmethod
    def neg(value: 'Expression | Stat | PlaceholderValue') -> 'Expression':
        return Expression.mul(value, -1)

    def __iadd__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.iadd(self, other)
        return self

    def __add__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.add(self, other)

    def __radd__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.radd(self, other)

    def __isub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.isub(self, other)
        return self

    def __sub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.sub(self, other)

    def __rsub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.rsub(self, other)

    def __imul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.imul(self, other)
        return self

    def __mul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.mul(self, other)

    def __rmul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.rmul(self, other)

    def __itruediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.itruediv(self, other)
        return self

    def __truediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.truediv(self, other)

    def __ifloordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.ifloordiv(self, other)
        return self

    def __floordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.truediv(self, other)

    def __neg__(self) -> 'Expression':
        return Expression.neg(self)

    def __str__(self) -> str:
        """Do NOT call this method when it is not used inside of a f-string! It will break things.
        
        The reason that this pushes is that you can make something like this work:
        ```py
        stat = PlayerStat('stat')
        chat(f'&aYour stat is &6{stat + 1}g')
        ```
        """
        EXPR_HANDLER.push()
        return str(self.fetch_stat_or_int(self.left))

    def __repr__(self) -> str:
        """Do NOT call this method when it is not used inside of a f-string! It will break things.
        
        The reason that this pushes is that you can make something like this work:
        ```py
        stat = PlayerStat('stat')
        chat(f'&aYour stat is &6{stat + 1}g')
        ```
        """
        EXPR_HANDLER.push()
        return repr(self.fetch_stat_or_int(self.left))

    def __eq__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Condition':
        return self._placeholder_value_cls.equals(self, other)

    def __ne__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'IfStatement':
        return self._placeholder_value_cls.not_equal(self, other)

    def __gt__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Condition':
        return self._placeholder_value_cls.greater_than(self, other)

    def __lt__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Condition':
        return self._placeholder_value_cls.less_than(self, other)

    def __ge__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Condition':
        return self._placeholder_value_cls.greater_than_or_equal(self, other)

    def __le__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Condition':
        return self._placeholder_value_cls.less_than_or_equal(self, other)
