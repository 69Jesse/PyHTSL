from .condition.conditional_statements import IfStatement
from .internal_type import InternalType
from .expression.handler import ExpressionHandler, EXPR_HANDLER
from .condition.base_condition import BaseCondition
from .condition.binary_condition import BinaryConditionOperator, BinaryCondition
from .expression.housing_type import (
    NumericHousingType,
    HousingType,
    _housing_type_as_right_side,
)
from .public.no_type_casting import no_type_casting

from abc import ABC, abstractmethod
import math

from typing import TYPE_CHECKING, Self, overload

if TYPE_CHECKING:
    from .editable import Editable
    from .expression.binary_expression import BinaryExpression, BinaryExpressionOperator
    from .expression.conditional_expressions import (
        ConditionalEnterExpression,
        ConditionalExitExpression,
    )
    from .stats.base_stat import BaseStat
    from .stats.temporary_stat import TemporaryStat
    from .placeholders import PlaceholderCheckable, PlaceholderEditable


__all__ = ('Checkable',)


def _transformed_to_long(
    value: 'Checkable | NumericHousingType',
) -> 'Checkable | NumericHousingType':
    if isinstance(value, Checkable):
        return value.as_long()
    if isinstance(value, NumericHousingType):
        return int(value)
    raise TypeError(f'Cannot transform {repr(value)} to long.')


def _transformed_to_double(
    value: 'Checkable | NumericHousingType',
) -> 'Checkable | NumericHousingType':
    if isinstance(value, Checkable):
        return value.as_double()
    if isinstance(value, NumericHousingType):
        return float(value)
    raise TypeError(f'Cannot transform {repr(value)} to double.')


def _transformed_to_string(
    value: 'Checkable | HousingType',
) -> 'Checkable | HousingType':
    if isinstance(value, Checkable):
        return value.as_string()
    if isinstance(value, HousingType):
        return str(value)
    raise TypeError(f'Cannot transform {repr(value)} to string.')


class Checkable(ABC):
    internal_type: InternalType = InternalType.ANY
    fallback_value: HousingType | None = None

    @staticmethod
    def _import_binary_expression(
        binary_expression_cls: type['BinaryExpression'],
        binary_operator_cls: type['BinaryExpressionOperator'],
    ) -> None:
        globals()[binary_expression_cls.__name__] = binary_expression_cls
        globals()[binary_operator_cls.__name__] = binary_operator_cls

    @staticmethod
    def _import_conditional_expressions(
        conditional_enter_expression_cls: type['ConditionalEnterExpression'],
        conditional_exit_expression_cls: type['ConditionalExitExpression'],
    ) -> None:
        globals()[conditional_enter_expression_cls.__name__] = (
            conditional_enter_expression_cls
        )
        globals()[conditional_exit_expression_cls.__name__] = (
            conditional_exit_expression_cls
        )

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
        return f'"{text}"' if ' ' in text else text  # ugly hack until htsw

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

    def equals(
        self, other: 'Checkable | HousingType', *, check_internal_type: bool = True
    ) -> bool:
        """
        Checks if the current object is equal to another object.
        """
        if not isinstance(other, Checkable):
            return False
        if check_internal_type:
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
    def _other_as_type_compatible(
        self, other: 'Editable', internal_type: InternalType | None = None
    ) -> 'Editable': ...

    @overload
    def _other_as_type_compatible(
        self, other: 'Checkable', internal_type: InternalType | None = None
    ) -> 'Checkable': ...

    @overload
    def _other_as_type_compatible(
        self, other: HousingType, internal_type: InternalType | None = None
    ) -> HousingType: ...

    @overload
    def _other_as_type_compatible(
        self,
        other: 'Checkable | HousingType',
        internal_type: InternalType | None = None,
    ) -> 'Checkable | HousingType': ...

    def _other_as_type_compatible(
        self,
        other: 'Checkable | HousingType',
        internal_type: InternalType | None = None,
    ) -> 'Checkable | HousingType':
        internal_type = internal_type or self.internal_type
        if internal_type is InternalType.ANY:
            return other

        if isinstance(other, BaseStat) and self.equals(
            other, check_internal_type=False
        ):
            return other

        if isinstance(other, Checkable):
            if internal_type is InternalType.LONG:
                other = other.as_long()
            elif internal_type is InternalType.DOUBLE:
                other = other.as_double()
            elif internal_type is InternalType.STRING:
                other = other.as_string()

        if isinstance(other, BinaryExpression):
            other._left = self._other_as_type_compatible(other._left)
            other._right = self._other_as_type_compatible(other._right)
            return other

        if isinstance(other, Checkable):
            if internal_type is InternalType.LONG and (
                other.internal_type is InternalType.ANY
                or other.internal_type is InternalType.LONG
            ):
                return _transformed_to_long(other)
            if internal_type is InternalType.DOUBLE and (
                other.internal_type is InternalType.ANY
                or other.internal_type is InternalType.DOUBLE
            ):
                return _transformed_to_double(other)
            if internal_type is InternalType.STRING and (
                other.internal_type is InternalType.ANY
                or other.internal_type is InternalType.STRING
            ):
                return _transformed_to_string(other)
        if isinstance(other, NumericHousingType):
            if internal_type is InternalType.LONG:
                return _transformed_to_long(other)
            if internal_type is InternalType.DOUBLE:
                return _transformed_to_double(other)
            if internal_type is InternalType.STRING:
                return _transformed_to_string(other)
        if internal_type is InternalType.STRING:
            return _transformed_to_string(other)
        raise TypeError(
            f'{repr(self)} with internal type {internal_type} '
            + f'is incompatible with {repr(other)}'
            + (
                f' with internal type {other.internal_type.name}'
                if isinstance(other, Checkable)
                else ''
            )
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
                copy.fallback_value = copy._other_as_type_compatible(
                    copy.fallback_value
                )
            except TypeError as exc:
                raise TypeError(
                    f'Cannot transform fallback value {repr(copy.fallback_value)} to internal type {type_.name}.'
                ) from exc
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

        return _housing_type_as_right_side(value) if value is not None else None

    def __add__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        temp_stat = TemporaryStat(self.internal_type)
        expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = BinaryExpression(
            temp_stat,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Increment,
        )
        EXPR_HANDLER.add(expr)
        return temp_stat

    def __radd__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        return self.__add__(other)

    def __sub__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        temp_stat = TemporaryStat(self.internal_type)
        expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = BinaryExpression(
            temp_stat,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Decrement,
        )
        EXPR_HANDLER.add(expr)
        return temp_stat

    def __rsub__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        temp_stat = TemporaryStat(self.internal_type)
        expr = BinaryExpression(
            temp_stat,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Set,
        )
        EXPR_HANDLER.add(expr)
        expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Decrement)
        EXPR_HANDLER.add(expr)
        return temp_stat

    def __mul__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        temp_stat = TemporaryStat(self.internal_type)
        expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = BinaryExpression(
            temp_stat,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Multiply,
        )
        EXPR_HANDLER.add(expr)
        return temp_stat

    def __rmul__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        return self.__mul__(other)

    def __truediv__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        temp_stat = TemporaryStat(self.internal_type)
        expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        expr = BinaryExpression(
            temp_stat,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Divide,
        )
        EXPR_HANDLER.add(expr)
        return temp_stat

    def __rtruediv__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        temp_stat = TemporaryStat(self.internal_type)
        expr = BinaryExpression(
            temp_stat,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Set,
        )
        EXPR_HANDLER.add(expr)
        expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Divide)
        EXPR_HANDLER.add(expr)
        return temp_stat

    def __floordiv__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        return self.__truediv__(other)

    def __rfloordiv__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        return self.__truediv__(other)

    def _pow_multiply_strat(self, other: int) -> 'TemporaryStat | int':
        if other == 0:
            return 1
        temp_stat = TemporaryStat(self.internal_type)
        expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        log2 = int(math.log2(other))
        for _ in range(log2):
            expr = BinaryExpression(
                temp_stat, temp_stat, BinaryExpressionOperator.Multiply
            )
            EXPR_HANDLER.add(expr)
        remaining = other - 2**log2
        if remaining == 0:
            return temp_stat
        if remaining == 1:
            expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Multiply)
            EXPR_HANDLER.add(expr)
            return temp_stat
        expr = BinaryExpression(
            temp_stat, self.__pow__(remaining), BinaryExpressionOperator.Multiply
        )
        EXPR_HANDLER.add(expr)
        return temp_stat

    def _pow_divide_strat(self, other: int) -> 'TemporaryStat | int':
        if other == 0:
            return 1
        temp_stat = TemporaryStat(self.internal_type)
        expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Set)
        EXPR_HANDLER.add(expr)
        log2 = int(math.log2(other))
        for _ in range(log2 + 1):
            expr = BinaryExpression(
                temp_stat, temp_stat, BinaryExpressionOperator.Multiply
            )
            EXPR_HANDLER.add(expr)
        remaining = 2 ** (log2 + 1) - other
        assert remaining > 0
        if remaining == 1:
            expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            return temp_stat
        if remaining == 2:
            expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Divide)
            EXPR_HANDLER.add(expr)
            return temp_stat
        if remaining & (remaining - 1) == 0:
            expr = BinaryExpression(
                temp_stat,
                Checkable._pow_multiply_strat(self, remaining),
                BinaryExpressionOperator.Divide,
            )
            EXPR_HANDLER.add(expr)
            return temp_stat
        expr = BinaryExpression(
            temp_stat, self.__pow__(remaining), BinaryExpressionOperator.Divide
        )
        EXPR_HANDLER.add(expr)
        return temp_stat

    def __pow__(self, other: int) -> 'TemporaryStat | int':
        other = self._other_as_type_compatible(other)  # type: ignore
        if other < 0:
            raise ValueError('Power must be greater than or equal to 0')

        before_length = len(EXPR_HANDLER._expressions)
        multiply_strat_temp_stat = Checkable._pow_multiply_strat(self, other)
        multiply_strat_after_length = len(EXPR_HANDLER._expressions)
        if multiply_strat_after_length - before_length <= 1:
            return multiply_strat_temp_stat

        multiply_expressions: list['BinaryExpression'] = []
        for _ in range(multiply_strat_after_length - before_length):
            multiply_expressions.append(EXPR_HANDLER._expressions.pop(before_length))  # type: ignore

        assert len(EXPR_HANDLER._expressions) == before_length
        divide_strat_temp_stat = Checkable._pow_divide_strat(self, other)
        divide_strat_after_length = len(EXPR_HANDLER._expressions)

        if divide_strat_after_length < multiply_strat_after_length:
            return divide_strat_temp_stat

        for _ in range(divide_strat_after_length - before_length):
            EXPR_HANDLER._expressions.pop()
        assert len(EXPR_HANDLER._expressions) == before_length
        EXPR_HANDLER._expressions.extend(multiply_expressions)
        return multiply_strat_temp_stat

    def remainder(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        temp_stat_1 = TemporaryStat(self.internal_type)
        expr = BinaryExpression(temp_stat_1, self, BinaryExpressionOperator.Set)
        EXPR_HANDLER.add(expr)

        internal_type = (
            self.internal_type
            if not (isinstance(other, (int, float)) and other.is_integer())
            else InternalType.LONG
        )

        temp_stat_2 = TemporaryStat(internal_type)
        expr = BinaryExpression(
            temp_stat_2, self.as_type(internal_type), BinaryExpressionOperator.Set
        )
        EXPR_HANDLER.add(expr)
        expr = BinaryExpression(
            temp_stat_2,
            self._other_as_type_compatible(other, internal_type=internal_type),
            BinaryExpressionOperator.Divide,
        )
        EXPR_HANDLER.add(expr)
        if internal_type is InternalType.DOUBLE:
            expr = BinaryExpression(
                temp_stat_2,
                temp_stat_2.as_long(),
                BinaryExpressionOperator.Set,
                is_self_cast=True,
            )
            EXPR_HANDLER.add(expr)
            expr = BinaryExpression(
                temp_stat_2,
                temp_stat_2.as_double(),
                BinaryExpressionOperator.Set,
                is_self_cast=True,
            )
            EXPR_HANDLER.add(expr)
        expr = BinaryExpression(
            temp_stat_2,
            self._other_as_type_compatible(other, internal_type=internal_type),
            BinaryExpressionOperator.Multiply,
        )
        EXPR_HANDLER.add(expr)

        expr = BinaryExpression(
            temp_stat_1,
            temp_stat_2.as_type(self.internal_type),
            BinaryExpressionOperator.Decrement,
        )
        EXPR_HANDLER.add(expr)
        return temp_stat_1

    def __mod__(self, other: 'Checkable | NumericHousingType') -> 'TemporaryStat':
        temp_stat = self.remainder(other)

        statement = IfStatement(conditions=[temp_stat < 0])
        expr = ConditionalEnterExpression(statement)
        EXPR_HANDLER.add(expr)
        expr = BinaryExpression(
            temp_stat,
            self._other_as_type_compatible(other),
            BinaryExpressionOperator.Increment,
        )
        EXPR_HANDLER.add(expr)
        expr = ConditionalExitExpression(statement)
        EXPR_HANDLER.add(expr)

        return temp_stat

    def __neg__(self) -> 'TemporaryStat':
        return self.__mul__(-1)

    def abs(self) -> 'TemporaryStat':
        temp_stat = TemporaryStat(self.internal_type)
        expr = BinaryExpression(temp_stat, self, BinaryExpressionOperator.Set)
        EXPR_HANDLER.add(expr)

        statement = IfStatement(conditions=[self < 0])
        expr = ConditionalEnterExpression(statement)
        EXPR_HANDLER.add(expr)
        expr = BinaryExpression(temp_stat, -1, BinaryExpressionOperator.Multiply)
        EXPR_HANDLER.add(expr)
        expr = ConditionalExitExpression(statement)
        EXPR_HANDLER.add(expr)

        return temp_stat

    def __abs__(self) -> 'TemporaryStat':
        return self.abs()

    def __eq__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return BinaryCondition(
            self, self._other_as_type_compatible(other), BinaryConditionOperator.Equal
        )

    def __ne__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return ~self.__eq__(other)

    def __gt__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return BinaryCondition(
            self,
            self._other_as_type_compatible(other),
            BinaryConditionOperator.GreaterThan,
        )

    def __lt__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return BinaryCondition(
            self,
            self._other_as_type_compatible(other),
            BinaryConditionOperator.LessThan,
        )

    def __ge__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return BinaryCondition(
            self,
            self._other_as_type_compatible(other),
            BinaryConditionOperator.GreaterThanOrEqual,
        )

    def __le__(self, other: 'Checkable | HousingType') -> BaseCondition:
        return BinaryCondition(
            self,
            self._other_as_type_compatible(other),
            BinaryConditionOperator.LessThanOrEqual,
        )

    @property
    def value(self) -> Self:
        return self

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError


ExpressionHandler._import_checkable(Checkable)
BinaryCondition._import_checkable(Checkable)
