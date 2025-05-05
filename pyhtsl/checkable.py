import math

from .expression.handler import ExpressionHandler, EXPR_HANDLER
from .condition.base_condition import BaseCondition
from .condition.double_sided_condition import DoubleSidedConditionOperator, DoubleSidedCondition
from .expression.housing_type import NumericHousingType, HousingType, _housing_type_as_right_side

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from .expression.assignment_expression import Expression, ExpressionOperator
    from .stats.temporary_stat import TemporaryStat


__all__ = (
    'Checkable',
)


class Checkable(ABC):
    @staticmethod
    def _import_expression(
        expression_cls: type['Expression'],
        expression_operator_cls: type['ExpressionOperator'],
    ) -> None:
        globals()[expression_cls.__name__] = expression_cls
        globals()[expression_operator_cls.__name__] = expression_operator_cls

    @staticmethod
    def _import_temporary_stat(
        temporary_stat_cls: type['TemporaryStat'],
    ) -> None:
        globals()[temporary_stat_cls.__name__] = temporary_stat_cls

    @abstractmethod
    def _in_assignment_left_side(self) -> str:
        """
        var foo = %var.player/bar%
        ^^^^^^^
        """
        raise NotImplementedError

    @abstractmethod
    def _in_assignment_right_side(self) -> str:
        """
        var foo = %var.player/bar%
                  ^^^^^^^^^^^^^^^^
        """
        raise NotImplementedError

    @abstractmethod
    def _in_comparison_left_side(self) -> str:
        """
        if and (var "foo" > "%var.player/bar%") {
                ^^^^^^^^^
        """
        raise NotImplementedError

    @abstractmethod
    def _in_comparison_right_side(self) -> str:
        """
        if and (var "foo" > "%var.player/bar%") {
                            ^^^^^^^^^^^^^^^^^^
        """
        raise NotImplementedError

    @abstractmethod
    def _as_string(self) -> str:
        """
        chat "hello %player.name%"
                    ^^^^^^^^^^^^^
        """
        raise NotImplementedError

    @abstractmethod
    def _equals(self, other: 'Checkable | HousingType') -> bool:
        raise NotImplementedError

    @staticmethod
    def _to_assignment_right_side(
        value: 'Checkable | HousingType',
    ) -> str:
        if isinstance(value, Checkable):
            return value._in_assignment_right_side()
        return _housing_type_as_right_side(value)

    @staticmethod
    def _to_comparison_right_side(
        value: 'Checkable | HousingType',
    ) -> str:
        if isinstance(value, Checkable):
            return value._in_comparison_right_side()
        return _housing_type_as_right_side(value)

    def __str__(self) -> str:
        return self._as_string()

    def as_long(self) -> str:
        return f'{self._as_string()}L'

    def as_double(self) -> str:
        return f'{self._as_string()}D'

    def as_string(self) -> str:
        return f'"{self._as_string()}"'

    @staticmethod
    def add(
        left: 'Checkable',
        right: 'Checkable | NumericHousingType',
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionOperator.Increment)
        EXPR_HANDLER.add(expr)
        return expr

    def __add__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.add(self, other)

    @staticmethod
    def radd(
        left: 'Checkable | NumericHousingType',
        right: 'Checkable',
    ) -> 'Expression':
        return Checkable.add(right, left)

    def __radd__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.radd(other, self)

    @staticmethod
    def sub(
        left: 'Checkable',
        right: 'Checkable | NumericHousingType',
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    def __sub__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.add(self, other)

    @staticmethod
    def rsub(
        left: 'Checkable | NumericHousingType',
        right: 'Checkable',
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.add(
            Expression(temp_stat, right, ExpressionOperator.Decrement),
        )
        return expr

    def __rsub__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.rsub(other, self)

    @staticmethod
    def mul(
        left: 'Checkable',
        right: 'Checkable | NumericHousingType',
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        return expr

    def __mul__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.mul(self, other)

    @staticmethod
    def rmul(
        left: 'Checkable | NumericHousingType',
        right: 'Checkable',
    ) -> 'Expression':
        return Checkable.mul(right, left)

    def __rmul__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.rmul(other, self)

    @staticmethod
    def truediv(
        left: 'Checkable',
        right: 'Checkable | NumericHousingType',
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, right, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        return expr

    def __truediv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.truediv(self, other)

    @staticmethod
    def rtruediv(
        left: 'Checkable | NumericHousingType',
        right: 'Checkable',
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.add(
            Expression(temp_stat, right, ExpressionOperator.Divide),
        )
        return expr

    def __rtruediv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.rtruediv(other, self)

    @staticmethod
    def floordiv(
        left: 'Checkable',
        right: 'Checkable | NumericHousingType',
    ) -> 'Expression':
        return Checkable.truediv(left, right)

    def __floordiv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.floordiv(self, other)

    @staticmethod
    def rfloordiv(
        left: 'Checkable | NumericHousingType',
        right: 'Checkable',
    ) -> 'Expression':
        return Checkable.rtruediv(left, right)

    def __rfloordiv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.rfloordiv(other, self)

    @staticmethod
    def _pow_multiply_strat(
        left: 'Checkable | NumericHousingType',
        right: int,
    ) -> 'Expression | int':
        if right == 0:
            return 1
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        log2 = int(math.log2(right))
        for _ in range(log2):
            expr = Expression(temp_stat, temp_stat, ExpressionOperator.Multiply)
            EXPR_HANDLER.add(expr)
        remaining = right - 2 ** log2
        if remaining == 0:
            return expr
        if remaining == 1:
            expr = Expression(temp_stat, left, ExpressionOperator.Multiply)
            EXPR_HANDLER.add(expr)
            return expr
        expr = Expression(temp_stat, Checkable.pow(left, remaining), ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def _pow_divide_strat(
        left: 'Checkable | NumericHousingType',
        right: int,
    ) -> 'Expression | int':
        if right == 0:
            return 1
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        log2 = int(math.log2(right))
        for _ in range(log2 + 1):
            expr = Expression(temp_stat, temp_stat, ExpressionOperator.Multiply)
            EXPR_HANDLER.add(expr)
        remaining = 2 ** (log2 + 1) - right
        assert remaining > 0
        if remaining == 1:
            expr = Expression(temp_stat, left, ExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            return expr
        if remaining == 2:
            expr = Expression(temp_stat, left, ExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            expr = Expression(temp_stat, left, ExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            return expr
        if remaining & (remaining - 1) == 0:
            expr = Expression(temp_stat, Checkable._pow_multiply_strat(left, remaining), ExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            return expr
        expr = Expression(temp_stat, Checkable.pow(left, remaining), ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def pow(
        left: 'Checkable | NumericHousingType',
        right: int,
    ) -> 'Expression | int':
        if right < 0:
            raise ValueError('Power must be greater than or equal to 0')

        before_length = len(EXPR_HANDLER._expressions)
        multiply_strat_expr = Checkable._pow_multiply_strat(left, right)
        multiply_strat_after_length = len(EXPR_HANDLER._expressions)
        if multiply_strat_after_length - before_length <= 1:
            return multiply_strat_expr

        multiply_expressions: list['Expression'] = []
        for _ in range(multiply_strat_after_length - before_length):
            multiply_expressions.append(EXPR_HANDLER._expressions.pop(before_length))

        assert len(EXPR_HANDLER._expressions) == before_length
        divide_strat_expr = Checkable._pow_divide_strat(left, right)
        divide_strat_after_length = len(EXPR_HANDLER._expressions)

        if divide_strat_after_length < multiply_strat_after_length:
            return divide_strat_expr

        for _ in range(divide_strat_after_length - before_length):
            EXPR_HANDLER._expressions.pop()
        assert len(EXPR_HANDLER._expressions) == before_length
        EXPR_HANDLER._expressions.extend(multiply_expressions)
        return multiply_strat_expr

    def __pow__(self, other: int) -> 'Expression | int':
        return Checkable.pow(self, other)

    @staticmethod
    def unsafemod(
        left: 'Checkable | NumericHousingType',
        right: 'Checkable | NumericHousingType',
    ) -> 'Expression':
        temp_stat_1 = TemporaryStat()
        expr = Expression(temp_stat_1, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        temp_stat_2 = TemporaryStat()
        expr = Expression(temp_stat_2, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, right, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, right, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, temp_stat_2, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def safemod(
        left: 'Checkable | NumericHousingType',
        right: 'Checkable | NumericHousingType',
    ) -> 'Expression':
        temp_stat_1 = TemporaryStat()
        expr = Expression(temp_stat_1, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, right, ExpressionOperator.Increment)
        EXPR_HANDLER.add(expr)
        temp_stat_2 = TemporaryStat()
        expr = Expression(temp_stat_2, left, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, right, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, right, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, temp_stat_2, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return Expression.unsafemod(expr, right)

    @staticmethod
    def mod(
        left: 'Checkable | NumericHousingType',
        right: 'Checkable | NumericHousingType',
    ) -> 'Expression':
        return Checkable.safemod(left, right)

    def __mod__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return Checkable.mod(self, other)

    @staticmethod
    def neg(value: 'Checkable') -> 'Expression':
        return Checkable.mul(value, -1)

    def __neg__(self) -> 'Expression':
        return Checkable.neg(self)

    @staticmethod
    def sign(
        value: 'Checkable',
        *,
        greater_than_2_62: bool = False,
        multiplied_by: int = 1,
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, value, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        if greater_than_2_62:
            expr = Expression(temp_stat, 2, ExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, 2 ** 62, ExpressionOperator.Increment)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, 2 ** 62, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, 2 * multiplied_by, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, 1 * multiplied_by, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    @staticmethod
    def abs(
        value: 'Checkable',
        *,
        greater_than_2_62: bool = False,
        sign: 'Expression | int | None' = None,
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, value, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(
            temp_stat,
            sign if sign is not None else Checkable.sign(value, greater_than_2_62=greater_than_2_62),
            ExpressionOperator.Multiply,
        )
        EXPR_HANDLER.add(expr)
        return expr

    def __abs__(self) -> 'Expression':
        return Checkable.abs(self)

    @staticmethod
    def equals(
        left: 'Checkable',
        right: 'Checkable | HousingType',
    ) -> BaseCondition:
        return DoubleSidedCondition(left, right, DoubleSidedConditionOperator.Equal)

    def __eq__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return Checkable.equals(self, other)

    @staticmethod
    def not_equal(
        left: 'Checkable',
        right: 'Checkable | HousingType',
    ) -> BaseCondition:
        return ~Checkable.equals(left, right)

    def __ne__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return Checkable.not_equal(self, other)

    @staticmethod
    def greater_than(
        left: 'Checkable',
        right: 'Checkable | HousingType',
    ) -> BaseCondition:
        return DoubleSidedCondition(left, right, DoubleSidedConditionOperator.GreaterThan)

    def __gt__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return Checkable.greater_than(self, other)

    @staticmethod
    def less_than(
        left: 'Checkable',
        right: 'Checkable | HousingType',
    ) -> BaseCondition:
        return DoubleSidedCondition(left, right, DoubleSidedConditionOperator.LessThan)

    def __lt__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return Checkable.less_than(self, other)

    @staticmethod
    def greater_than_or_equal(
        left: 'Checkable',
        right: 'Checkable | HousingType',
    ) -> BaseCondition:
        return DoubleSidedCondition(left, right, DoubleSidedConditionOperator.GreaterThanOrEqual)

    def __ge__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return Checkable.greater_than_or_equal(self, other)

    @staticmethod
    def less_than_or_equal(
        left: 'Checkable',
        right: 'Checkable | HousingType',
    ) -> BaseCondition:
        return DoubleSidedCondition(left, right, DoubleSidedConditionOperator.LessThanOrEqual)

    def __le__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return Checkable.less_than_or_equal(self, other)

    @property
    def value(self) -> Self:
        return self


ExpressionHandler._import_checkable(Checkable)
DoubleSidedCondition._import_checkable(Checkable)
