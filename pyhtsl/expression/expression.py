import os
import math

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
        left: 'Expression | Stat | int | PlaceholderValue',
        right: 'Expression | Stat | PlaceholderValue',
    ) -> 'Expression':
        return Expression.add(right, left)

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
        left: 'Expression | Stat | int | PlaceholderValue',
        right: 'Expression | Stat | PlaceholderValue',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.add(
            Expression(temp_stat, right, ExpressionType.Decrement),
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
        left: 'Expression | Stat | int | PlaceholderValue',
        right: 'Expression | Stat | PlaceholderValue',
    ) -> 'Expression':
        return Expression.mul(right, left)

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
    def rtruediv(
        left: 'Expression | Stat | int | PlaceholderValue',
        right: 'Expression | Stat | PlaceholderValue',
    ) -> 'Expression':
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.add(
            Expression(temp_stat, right, ExpressionType.Divide),
        )
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
    def rfloordiv(
        left: 'Expression | Stat | int | PlaceholderValue',
        right: 'Expression | Stat | PlaceholderValue',
    ) -> 'Expression':
        return Expression.rtruediv(left, right)

    @staticmethod
    def ipow(
        left: 'Expression | Stat',
        right: int,
    ) -> None:
        return Expression.set(left, Expression.pow(left, right))

    @staticmethod
    def _pow_multiply_strat(
        left: 'Expression | Stat | PlaceholderValue',
        right: int,
    ) -> 'Expression | int':
        if right == 0:
            return 1
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        log2 = int(math.log2(right))
        for _ in range(log2):
            expr = Expression(temp_stat, temp_stat, ExpressionType.Multiply)
            EXPR_HANDLER.add(expr)
        remaining = right - 2 ** log2
        if remaining == 0:
            return expr
        if remaining == 1:
            expr = Expression(temp_stat, left, ExpressionType.Multiply)
            EXPR_HANDLER.add(expr)
            return expr
        expr = Expression(temp_stat, Expression.pow(left, remaining), ExpressionType.Multiply)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def _pow_divide_strat(
        left: 'Expression | Stat | PlaceholderValue',
        right: int,
    ) -> 'Expression | int':
        if right == 0:
            return 1
        temp_stat = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        log2 = int(math.log2(right))
        for _ in range(log2 + 1):
            expr = Expression(temp_stat, temp_stat, ExpressionType.Multiply)
            EXPR_HANDLER.add(expr)
        remaining = 2 ** (log2 + 1) - right
        assert remaining > 0
        if remaining == 1:
            expr = Expression(temp_stat, left, ExpressionType.Divide)
            EXPR_HANDLER.add(expr)
            return expr
        if remaining == 2:
            expr = Expression(temp_stat, left, ExpressionType.Divide)
            EXPR_HANDLER.add(expr)
            expr = Expression(temp_stat, left, ExpressionType.Divide)
            EXPR_HANDLER.add(expr)
            return expr
        if remaining & (remaining - 1) == 0:
            expr = Expression(temp_stat, Expression._pow_multiply_strat(left, remaining), ExpressionType.Divide)
            EXPR_HANDLER.add(expr)
            return expr
        expr = Expression(temp_stat, Expression.pow(left, remaining), ExpressionType.Divide)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def pow(
        left: 'Expression | Stat | PlaceholderValue',
        right: int,
    ) -> 'Expression | int':
        if right < 0:
            raise ValueError('Power must be greater than or equal to 0')

        before_length = len(EXPR_HANDLER._expressions)
        multiply_strat_expr = Expression._pow_multiply_strat(left, right)
        multiply_strat_after_length = len(EXPR_HANDLER._expressions)
        if multiply_strat_after_length - before_length <= 1:
            return multiply_strat_expr

        multiply_expressions: list['Expression'] = []
        for _ in range(multiply_strat_after_length - before_length):
            multiply_expressions.append(EXPR_HANDLER._expressions.pop(before_length))

        assert len(EXPR_HANDLER._expressions) == before_length
        divide_strat_expr = Expression._pow_divide_strat(left, right)
        divide_strat_after_length = len(EXPR_HANDLER._expressions)

        if divide_strat_after_length < multiply_strat_after_length:
            return divide_strat_expr

        for _ in range(divide_strat_after_length - before_length):
            EXPR_HANDLER._expressions.pop()
        assert len(EXPR_HANDLER._expressions) == before_length
        EXPR_HANDLER._expressions.extend(multiply_expressions)
        return multiply_strat_expr

    @staticmethod
    def imod(
        left: 'Expression | Stat',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> None:
        Expression.set(left, Expression.mod(left, right))

    @staticmethod
    def mod(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        temp_stat_1 = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat_1, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, right, ExpressionType.Increment)
        EXPR_HANDLER.add(expr)
        temp_stat_2 = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat_2, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, right, ExpressionType.Divide)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, right, ExpressionType.Multiply)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, temp_stat_2, ExpressionType.Decrement)
        EXPR_HANDLER.add(expr)
        return Expression.unsafemod(expr, right)

    @staticmethod
    def safemod(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        return Expression.mod(left, right)

    @staticmethod
    def unsafemod(
        left: 'Expression | Stat | PlaceholderValue',
        right: 'Expression | Stat | int | PlaceholderValue',
    ) -> 'Expression':
        temp_stat_1 = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat_1, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        temp_stat_2 = EXPR_HANDLER.temporary_stat_cls()
        expr = Expression(temp_stat_2, left, ExpressionType.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, right, ExpressionType.Divide)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, right, ExpressionType.Multiply)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, temp_stat_2, ExpressionType.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def neg(value: 'Expression | Stat | PlaceholderValue') -> 'Expression':
        return Expression.mul(value, -1)

    def __iadd__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.iadd(self, other)
        return self

    def __add__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.add(self, other)

    def __radd__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.radd(other, self)

    def __isub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.isub(self, other)
        return self

    def __sub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.sub(self, other)

    def __rsub__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.rsub(other, self)

    def __imul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.imul(self, other)
        return self

    def __mul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.mul(self, other)

    def __rmul__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.rmul(other, self)

    def __itruediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.itruediv(self, other)
        return self

    def __truediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.truediv(self, other)

    def __rtruediv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.rtruediv(other, self)

    def __ifloordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.ifloordiv(self, other)
        return self

    def __floordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.floordiv(self, other)

    def __rfloordiv__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.rfloordiv(other, self)

    def __ipow__(self, other: int) -> 'Self':
        Expression.ipow(self, other)
        return self

    def __pow__(self, other: int) -> 'Expression | int':
        return Expression.pow(self, other)

    def __imod__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Self':
        Expression.imod(self, other)
        return self

    def __mod__(self, other: 'Expression | Stat | int | PlaceholderValue') -> 'Expression':
        return Expression.mod(self, other)

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
