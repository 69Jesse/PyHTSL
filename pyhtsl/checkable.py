import math
from enum import Enum

from .expression.handler import ExpressionHandler, EXPR_HANDLER
from .condition.base_condition import BaseCondition
from .condition.double_sided_condition import DoubleSidedConditionOperator, DoubleSidedCondition
from .expression.housing_type import NumericHousingType, HousingType, _housing_type_as_right_side

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from .expression.assignment_expression import Expression, ExpressionOperator
    from .stats.temporary_stat import TemporaryStat
    from .placeholders import PlaceholderCheckable, PlaceholderEditable


__all__ = (
    'Checkable',
)


class InternalType(Enum):
    ANY = 0
    LONG = 1
    DOUBLE = 2
    STRING = 3


def _formatted_as_long(value: 'Checkable | NumericHousingType') -> 'Checkable | NumericHousingType':
    if isinstance(value, Checkable):
        return value  # TODO when typecasts are implemented
    if isinstance(value, NumericHousingType):
        return int(value)
    raise TypeError(f'Cannot format {repr(value)} as long.')


def _formatted_as_double(value: 'Checkable | NumericHousingType') -> 'Checkable | NumericHousingType':
    if isinstance(value, Checkable):
        return value  # TODO when typecasts are implemented
    if isinstance(value, NumericHousingType):
        return float(value)
    raise TypeError(f'Cannot format {repr(value)} as double.')


def _formatted_as_string(value: 'Checkable | HousingType') -> 'Checkable | HousingType':
    if isinstance(value, Checkable):
        return value  # TODO when typecasts are implemented
    if isinstance(value, HousingType):
        return str(value)
    raise TypeError(f'Cannot format {repr(value)} as string.')


class Checkable(ABC):
    internal_type: InternalType = InternalType.ANY

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

    @staticmethod
    def _import_placeholders(
        placeholder_checkable_cls: type['PlaceholderCheckable'],
        placeholder_editable_cls: type['PlaceholderEditable'],
    ) -> None:
        globals()[placeholder_checkable_cls.__name__] = placeholder_checkable_cls
        globals()[placeholder_editable_cls.__name__] = placeholder_editable_cls

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
        # TODO fix when typecasts are implemented
        if isinstance(value, (PlaceholderCheckable, PlaceholderEditable)):
            result = value._in_assignment_right_side()
            if value.internal_type is InternalType.LONG:
                result = f'{result}L'
            elif value.internal_type is InternalType.DOUBLE:
                result = f'{result}D'
            elif value.internal_type is InternalType.STRING:
                result = f'"{result}"'
            return result

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

    def _other_as_type_compatible(self, other: 'Checkable | HousingType') -> 'Checkable | HousingType':
        if self.internal_type is InternalType.ANY:
            return other
        if isinstance(other, Checkable):
            if self.internal_type is InternalType.LONG and (other.internal_type is InternalType.ANY or other.internal_type is InternalType.LONG):
                return _formatted_as_long(other)
            if self.internal_type is InternalType.DOUBLE and (other.internal_type is InternalType.ANY or other.internal_type is InternalType.DOUBLE):
                return _formatted_as_double(other)
            if self.internal_type is InternalType.STRING and (other.internal_type is InternalType.ANY or other.internal_type is InternalType.STRING):
                return _formatted_as_string(other)
        if isinstance(other, NumericHousingType):
            if self.internal_type is InternalType.LONG:
                return _formatted_as_long(other)
            if self.internal_type is InternalType.DOUBLE:
                return _formatted_as_double(other)
            if self.internal_type is InternalType.STRING:
                return _formatted_as_string(other)
        if self.internal_type is InternalType.STRING:
            return _formatted_as_string(other)
        raise TypeError(
            f'{repr(self)} with internal type {self.internal_type} '
            + f'is incompatible with {repr(other)}'
            + (f' with internal type {other.internal_type}' if isinstance(other, Checkable) else '')
        )

    def is_type_compatible(self, other: 'Checkable | HousingType') -> bool:
        try:
            self._other_as_type_compatible(other)
        except TypeError:
            return False
        return True

    def _assert_type_compatible(self, other: 'Checkable | HousingType') -> None:
        self._other_as_type_compatible(other)
        if isinstance(other, Checkable):
            other._other_as_type_compatible(self)

    @abstractmethod
    def copied(self) -> Self:
        """
        Returns a copy of the current object.
        """
        raise NotImplementedError

    def as_long(self) -> Self:
        """
        Creates a copy of the current object, with the internal type set to LONG.
        """
        copy = self.copied()
        copy.internal_type = InternalType.LONG
        return copy

    def as_double(self) -> Self:
        """
        Creates a copy of the current object, with the internal type set to DOUBLE.
        """
        copy = self.copied()
        copy.internal_type = InternalType.DOUBLE
        return copy

    def as_string(self) -> Self:
        """
        Creates a copy of the current object, with the internal type set to STRING.
        """
        copy = self.copied()
        copy.internal_type = InternalType.STRING
        return copy

    def as_any(self) -> Self:
        """
        Creates a copy of the current object, with the internal type set to ANY.
        """
        copy = self.copied()
        copy.internal_type = InternalType.ANY
        return copy

    def __add__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        self._assert_type_compatible(other)
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, other, ExpressionOperator.Increment)
        EXPR_HANDLER.add(expr)
        return expr

    def __radd__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return self.__add__(other)

    def __sub__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        self._assert_type_compatible(other)
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, other, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    def __rsub__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        self._assert_type_compatible(other)
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, other, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.add(
            Expression(temp_stat, self, ExpressionOperator.Decrement),
        )
        return expr

    def __mul__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        self._assert_type_compatible(other)
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, other, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        return expr

    def __rmul__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return self.__mul__(other)

    def __truediv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        self._assert_type_compatible(other)
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, other, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        return expr

    def __rtruediv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        self._assert_type_compatible(other)
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, other, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.add(
            Expression(temp_stat, self, ExpressionOperator.Divide),
        )
        return expr

    def __floordiv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return self.__truediv__(other)

    def __rfloordiv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return self.__truediv__(other)

    def _pow_multiply_strat(self, other: int) -> 'Expression | int':
        if other == 0:
            return 1
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        log2 = int(math.log2(other))
        for _ in range(log2):
            expr = Expression(temp_stat, temp_stat, ExpressionOperator.Multiply)
            EXPR_HANDLER.add(expr)
        remaining = other - 2 ** log2
        if remaining == 0:
            return expr
        if remaining == 1:
            expr = Expression(temp_stat, self, ExpressionOperator.Multiply)
            EXPR_HANDLER.add(expr)
            return expr
        expr = Expression(temp_stat, self.__pow__(remaining), ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        return expr

    def _pow_divide_strat(self, other: int) -> 'Expression | int':
        if other == 0:
            return 1
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        log2 = int(math.log2(other))
        for _ in range(log2 + 1):
            expr = Expression(temp_stat, temp_stat, ExpressionOperator.Multiply)
            EXPR_HANDLER.add(expr)
        remaining = 2 ** (log2 + 1) - other
        assert remaining > 0
        if remaining == 1:
            expr = Expression(temp_stat, self, ExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            return expr
        if remaining == 2:
            expr = Expression(temp_stat, self, ExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            expr = Expression(temp_stat, self, ExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            return expr
        if remaining & (remaining - 1) == 0:
            expr = Expression(temp_stat, Checkable._pow_multiply_strat(self, remaining), ExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            return expr
        expr = Expression(temp_stat, self.__pow__(remaining), ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        return expr

    def __pow__(self, other: int) -> 'Expression | int':
        self._assert_type_compatible(other)
        if other < 0:
            raise ValueError('Power must be greater than or equal to 0')

        before_length = len(EXPR_HANDLER._expressions)
        multiply_strat_expr = Checkable._pow_multiply_strat(self, other)
        multiply_strat_after_length = len(EXPR_HANDLER._expressions)
        if multiply_strat_after_length - before_length <= 1:
            return multiply_strat_expr

        multiply_expressions: list['Expression'] = []
        for _ in range(multiply_strat_after_length - before_length):
            multiply_expressions.append(EXPR_HANDLER._expressions.pop(before_length))

        assert len(EXPR_HANDLER._expressions) == before_length
        divide_strat_expr = Checkable._pow_divide_strat(self, other)
        divide_strat_after_length = len(EXPR_HANDLER._expressions)

        if divide_strat_after_length < multiply_strat_after_length:
            return divide_strat_expr

        for _ in range(divide_strat_after_length - before_length):
            EXPR_HANDLER._expressions.pop()
        assert len(EXPR_HANDLER._expressions) == before_length
        EXPR_HANDLER._expressions.extend(multiply_expressions)
        return multiply_strat_expr

    def unsafemod(self, other: 'Checkable | int') -> 'Expression':
        self._assert_type_compatible(other)
        temp_stat_1 = TemporaryStat()
        expr = Expression(temp_stat_1, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        temp_stat_2 = TemporaryStat()
        expr = Expression(temp_stat_2, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, other, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, other, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, temp_stat_2, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    def safemod(self, other: 'Checkable | int') -> 'Expression':
        self._assert_type_compatible(other)
        temp_stat_1 = TemporaryStat()
        expr = Expression(temp_stat_1, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, other, ExpressionOperator.Increment)
        EXPR_HANDLER.add(expr)
        temp_stat_2 = TemporaryStat()
        expr = Expression(temp_stat_2, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, other, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, other, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, temp_stat_2, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return Expression.unsafemod(expr, other)

    def __mod__(self, other: 'Checkable | int') -> 'Expression':
        return self.safemod(other)

    def __neg__(self) -> 'Expression':
        return self.__mul__(-1)

    def sign(
        self,
        *,
        greater_than_2_62: bool = False,
        multiplied_by: int = 1,
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
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

    def abs(
        self,
        *,
        greater_than_2_62: bool = False,
        sign: 'Expression | int | None' = None,
    ) -> 'Expression':
        temp_stat = TemporaryStat()
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(
            temp_stat,
            sign if sign is not None else Checkable.sign(self, greater_than_2_62=greater_than_2_62),
            ExpressionOperator.Multiply,
        )
        EXPR_HANDLER.add(expr)
        return expr

    def __abs__(self) -> 'Expression':
        return self.abs()

    def __eq__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return DoubleSidedCondition(self, self._other_as_type_compatible(other), DoubleSidedConditionOperator.Equal)

    def __ne__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return ~self.__eq__(other)

    def __gt__(self, other: 'Checkable | HousingType') -> BaseCondition:
        self._assert_type_compatible(other)
        return DoubleSidedCondition(self, self._other_as_type_compatible(other), DoubleSidedConditionOperator.GreaterThan)

    def __lt__(self, other: 'Checkable | HousingType') -> BaseCondition:
        self._assert_type_compatible(other)
        return DoubleSidedCondition(self, self._other_as_type_compatible(other), DoubleSidedConditionOperator.LessThan)

    def __ge__(self, other: 'Checkable | HousingType') -> BaseCondition:
        self._assert_type_compatible(other)
        return DoubleSidedCondition(self, self._other_as_type_compatible(other), DoubleSidedConditionOperator.GreaterThanOrEqual)

    def __le__(self, other: 'Checkable | HousingType') -> BaseCondition:
        self._assert_type_compatible(other)
        return DoubleSidedCondition(self, self._other_as_type_compatible(other), DoubleSidedConditionOperator.LessThanOrEqual)

    @property
    def value(self) -> Self:
        return self


ExpressionHandler._import_checkable(Checkable)
DoubleSidedCondition._import_checkable(Checkable)
