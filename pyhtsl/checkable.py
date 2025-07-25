import math

from .internal_type import InternalType
from .expression.handler import ExpressionHandler, EXPR_HANDLER
from .condition.base_condition import BaseCondition
from .condition.double_sided_condition import DoubleSidedConditionOperator, DoubleSidedCondition
from .expression.housing_type import NumericHousingType, HousingType, _housing_type_as_right_side
from .public.no_type_casting import no_type_casting

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Self, overload
if TYPE_CHECKING:
    from .editable import Editable
    from .expression.assignment_expression import Expression, ExpressionOperator
    from .stats.base_stat import BaseStat
    from .stats.temporary_stat import TemporaryStat
    from .placeholders import PlaceholderCheckable, PlaceholderEditable


__all__ = (
    'Checkable',
)


def _transformed_to_long(value: 'Checkable | NumericHousingType') -> 'Checkable | NumericHousingType':
    if isinstance(value, Checkable):
        return value.as_long()
    if isinstance(value, NumericHousingType):
        return int(value)
    raise TypeError(f'Cannot transform {repr(value)} to long.')


def _transformed_to_double(value: 'Checkable | NumericHousingType') -> 'Checkable | NumericHousingType':
    if isinstance(value, Checkable):
        return value.as_double()
    if isinstance(value, NumericHousingType):
        return float(value)
    raise TypeError(f'Cannot transform {repr(value)} to double.')


def _transformed_to_string(value: 'Checkable | HousingType') -> 'Checkable | HousingType':
    if isinstance(value, Checkable):
        return value.as_string()
    if isinstance(value, HousingType):
        return str(value)
    raise TypeError(f'Cannot transform {repr(value)} to string.')


class Checkable(ABC):
    internal_type: InternalType = InternalType.ANY
    fallback_value: HousingType | None = None

    @staticmethod
    def _import_expression(
        expression_cls: type['Expression'],
        expression_operator_cls: type['ExpressionOperator'],
    ) -> None:
        globals()[expression_cls.__name__] = expression_cls
        globals()[expression_operator_cls.__name__] = expression_operator_cls

    @staticmethod
    def _import_base_stat(
        base_stat_cls: type['BaseStat'],
    ) -> None:
        globals()[base_stat_cls.__name__] = base_stat_cls

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

    def _formatted_with_internal_type(
        self,
        text: str,
        *,
        include_internal_type: bool,
    ) -> str:
        if include_internal_type and not no_type_casting():
            if self.internal_type is InternalType.LONG:
                text += 'L'
            elif self.internal_type is InternalType.DOUBLE:
                text += 'D'
        return f'"{text}"'

    @abstractmethod
    def _in_assignment_left_side(self) -> str:
        """
        var foo = %var.player/bar%
        ^^^^^^^
        """
        raise NotImplementedError

    @abstractmethod
    def _in_assignment_right_side(self, *, include_internal_type: bool = True) -> str:
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
    def _as_string(self, include_fallback_value: bool = True) -> str:
        """
        chat "hello %player.name%"
                    ^^^^^^^^^^^^^
        """
        raise NotImplementedError

    @abstractmethod
    def _equals(self, other: 'Checkable | HousingType') -> bool:
        raise NotImplementedError

    def equals(self, other: 'Checkable | HousingType') -> bool:
        """
        Checks if the current object is equal to another object.
        """
        if not isinstance(other, Checkable):
            return False
        if self.internal_type is not other.internal_type:
            return False
        if self.fallback_value != other.fallback_value:
            return False
        return self._equals(other)

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

    @overload
    def _other_as_type_compatible(self, other: 'Editable') -> 'Editable':
        ...

    @overload
    def _other_as_type_compatible(self, other: 'Checkable') -> 'Checkable':
        ...

    @overload
    def _other_as_type_compatible(self, other: HousingType) -> HousingType:
        ...

    @overload
    def _other_as_type_compatible(self, other: 'Checkable | HousingType') -> 'Checkable | HousingType':
        ...

    def _other_as_type_compatible(self, other: 'Checkable | HousingType') -> 'Checkable | HousingType':
        if self.internal_type is InternalType.ANY:
            return other

        if isinstance(other, BaseStat) and not other.should_force_type_compatible:
            return other

        if isinstance(other, Checkable):
            if self.internal_type is InternalType.LONG:
                other = other.as_long()
            elif self.internal_type is InternalType.DOUBLE:
                other = other.as_double()
            elif self.internal_type is InternalType.STRING:
                other = other.as_string()

        if isinstance(other, Expression):
            other.left = self._other_as_type_compatible(other.left)
            other.right = self._other_as_type_compatible(other.right)
            return other

        if isinstance(other, Checkable):
            if self.internal_type is InternalType.LONG and (other.internal_type is InternalType.ANY or other.internal_type is InternalType.LONG):
                return _transformed_to_long(other)
            if self.internal_type is InternalType.DOUBLE and (other.internal_type is InternalType.ANY or other.internal_type is InternalType.DOUBLE):
                return _transformed_to_double(other)
            if self.internal_type is InternalType.STRING and (other.internal_type is InternalType.ANY or other.internal_type is InternalType.STRING):
                return _transformed_to_string(other)
        if isinstance(other, NumericHousingType):
            if self.internal_type is InternalType.LONG:
                return _transformed_to_long(other)
            if self.internal_type is InternalType.DOUBLE:
                return _transformed_to_double(other)
            if self.internal_type is InternalType.STRING:
                return _transformed_to_string(other)
        if self.internal_type is InternalType.STRING:
            return _transformed_to_string(other)
        raise TypeError(
            f'{repr(self)} with internal type {self.internal_type} '
            + f'is incompatible with {repr(other)}'
            + (f' with internal type {other.internal_type.name}' if isinstance(other, Checkable) else '')
        )

    def is_type_compatible(self, other: 'Checkable | HousingType') -> bool:
        try:
            self._other_as_type_compatible(other)
        except TypeError:
            return False
        return True

    @abstractmethod
    def _copied(self) -> Self:
        raise NotImplementedError

    def copied(self) -> Self:
        """
        Returns a copy of the current object.
        """
        copy = self._copied()
        copy.internal_type = self.internal_type
        copy.fallback_value = self.fallback_value
        return copy

    def as_type(self, type_: InternalType) -> Self:
        """
        Creates a copy of the current object, with the internal type set to the specified type.
        """
        copy = self.copied()
        copy.internal_type = type_
        if copy.fallback_value is not None:
            try:
                copy.fallback_value = copy._other_as_type_compatible(copy.fallback_value)
            except TypeError as exc:
                raise TypeError(f'Cannot transform fallback value {repr(copy.fallback_value)} to internal type {type_.name}.') from exc
        return copy

    def as_long(self) -> Self:
        """
        Creates a copy of the current object, with the internal type set to LONG.
        """
        return self.as_type(InternalType.LONG)

    def as_double(self) -> Self:
        """
        Creates a copy of the current object, with the internal type set to DOUBLE.
        """
        return self.as_type(InternalType.DOUBLE)

    def as_string(self) -> Self:
        """
        Creates a copy of the current object, with the internal type set to STRING.
        """
        return self.as_type(InternalType.STRING)

    def as_any(self) -> Self:
        """
        Creates a copy of the current object, with the internal type set to ANY.
        """
        return self.as_type(InternalType.ANY)

    def with_fallback(self, fallback_value: HousingType) -> Self:
        """
        Creates a copy of the current object, with the fallback value set to the specified value.
        """
        copy = self.copied()
        copy.fallback_value = copy._other_as_type_compatible(fallback_value)
        return copy

    def _get_formatted_fallback_value(self) -> str | None:
        value: HousingType | None = self.fallback_value
        if value is None:
            if self.internal_type is InternalType.LONG:
                value = 0
            elif self.internal_type is InternalType.DOUBLE:
                value = 0.0
            elif self.internal_type is InternalType.STRING:
                value = ''

        # HTSL doesnt let me escape quotes and I think this works since it defaults to empty string if its unset :D
        if isinstance(value, str):
            return value or None

        return _housing_type_as_right_side(value) if value is not None else None

    def __add__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        temp_stat = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, self._other_as_type_compatible(other), ExpressionOperator.Increment)
        EXPR_HANDLER.add(expr)
        return expr

    def __radd__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return self.__add__(other)

    def __sub__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        temp_stat = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, self._other_as_type_compatible(other), ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    def __rsub__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        temp_stat = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat, self._other_as_type_compatible(other), ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        EXPR_HANDLER.add(
            Expression(temp_stat, self, ExpressionOperator.Decrement),
        )
        return expr

    def __mul__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        temp_stat = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, self._other_as_type_compatible(other), ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        return expr

    def __rmul__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return self.__mul__(other)

    def __truediv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        temp_stat = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat, self._other_as_type_compatible(other), ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        return expr

    def __rtruediv__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        temp_stat = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat, self._other_as_type_compatible(other), ExpressionOperator.Set)
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
        temp_stat = TemporaryStat(self.internal_type)
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
        temp_stat = TemporaryStat(self.internal_type)
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
        other = self._other_as_type_compatible(other)  # type: ignore
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

    def unsafemod(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        other = self._other_as_type_compatible(other)  # type: ignore
        temp_stat_1 = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat_1, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        temp_stat_2 = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat_2, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, other, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        if self.internal_type is InternalType.DOUBLE or isinstance(other, float):
            temp_stat_2_copied = temp_stat_2.copied().as_long()
            temp_stat_2_copied.should_force_type_compatible = False
            expr = Expression(temp_stat_2.as_any(), temp_stat_2_copied, ExpressionOperator.Set)
            EXPR_HANDLER.add(expr)
            temp_stat_2_copied = temp_stat_2.copied().as_double()
            temp_stat_2_copied.should_force_type_compatible = False
            expr = Expression(temp_stat_2.as_any(), temp_stat_2_copied, ExpressionOperator.Set)
            EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, other, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, temp_stat_2, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return expr

    def safemod(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        other = self._other_as_type_compatible(other)  # type: ignore
        temp_stat_1 = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat_1, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, other, ExpressionOperator.Increment)
        EXPR_HANDLER.add(expr)
        temp_stat_2 = TemporaryStat(self.internal_type)
        expr = Expression(temp_stat_2, self, ExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, other, ExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        if self.internal_type is InternalType.DOUBLE or isinstance(other, float):
            temp_stat_2_copied = temp_stat_2.copied().as_long()
            temp_stat_2_copied.should_force_type_compatible = False
            expr = Expression(temp_stat_2.as_any(), temp_stat_2_copied, ExpressionOperator.Set)
            EXPR_HANDLER.add(expr)
            temp_stat_2_copied = temp_stat_2.copied().as_double()
            temp_stat_2_copied.should_force_type_compatible = False
            expr = Expression(temp_stat_2.as_any(), temp_stat_2_copied, ExpressionOperator.Set)
            EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_2, other, ExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        expr = Expression(temp_stat_1, temp_stat_2, ExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return Expression.unsafemod(expr, other)

    def __mod__(self, other: 'Checkable | NumericHousingType') -> 'Expression':
        return self.safemod(other)

    def __neg__(self) -> 'Expression':
        return self.__mul__(-1)

    def sign(
        self,
        *,
        greater_than_2_62: bool = False,
        multiplied_by: int = 1,
    ) -> 'Expression':
        temp_stat = TemporaryStat(self.internal_type)
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
        temp_stat = TemporaryStat(self.internal_type)
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
        return DoubleSidedCondition(self, self._other_as_type_compatible(other), DoubleSidedConditionOperator.GreaterThan)

    def __lt__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return DoubleSidedCondition(self, self._other_as_type_compatible(other), DoubleSidedConditionOperator.LessThan)

    def __ge__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return DoubleSidedCondition(self, self._other_as_type_compatible(other), DoubleSidedConditionOperator.GreaterThanOrEqual)

    def __le__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return DoubleSidedCondition(self, self._other_as_type_compatible(other), DoubleSidedConditionOperator.LessThanOrEqual)

    @property
    def value(self) -> Self:
        return self

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError


ExpressionHandler._import_checkable(Checkable)
DoubleSidedCondition._import_checkable(Checkable)
