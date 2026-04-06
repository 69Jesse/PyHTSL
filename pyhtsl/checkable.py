import re
from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar, Literal, Self, final, overload

from .actions.no_type_casting import no_type_casting
from .base_object import BaseObject
from .execute.backend_type import BackendType, into_backend_type
from .expression.condition.comparison_condition import (
    ComparisonCondition,
    ComparisonOperator,
)
from .expression.housing_type import (
    HousingType,
    NumericHousingType,
    housing_type_as_rhs,
)
from .internal_type import InternalType
from .utils.warn import warn

if TYPE_CHECKING:
    from .expression.binary_expression import BinaryExpression
    from .expression.compound_expression import CompoundExpression


__all__ = ('Checkable',)


class Checkable(BaseObject):
    pattern: ClassVar[re.Pattern[str] | None] = None
    pattern_factory: ClassVar[Callable[[re.Match[str]], 'Checkable'] | None] = None

    def __init_subclass__(
        cls,
        *,
        pattern: re.Pattern[str] | None = None,
        pattern_factory: Callable[[re.Match[str]], 'Checkable'] | None = None,
    ) -> None:
        super().__init_subclass__()
        if pattern is not None:
            assert pattern_factory is not None, (
                'pattern_factory must be provided if pattern is provided'
            )
        cls.pattern = pattern
        cls.pattern_factory = pattern_factory

    internal_type: InternalType = InternalType.ANY
    fallback_value: HousingType | None

    def __init__(
        self,
        *,
        internal_type: InternalType = InternalType.ANY,
        fallback_value: HousingType | None = None,
    ) -> None:
        self.internal_type = internal_type
        self.fallback_value = fallback_value

    def into_hashable(self) -> tuple[object, ...]:
        return (self.__class__,)

    def get_backend_fallback_value(self) -> BackendType | None:
        if self.fallback_value is None:
            return None
        return into_backend_type(self.fallback_value)

    def format_with_internal_type(
        self,
        text: str,
        *,
        include_internal_type: bool,
    ) -> str:
        if (
            not include_internal_type
            or no_type_casting()
            or self.internal_type is InternalType.ANY
        ):
            return text
        if self.internal_type is InternalType.LONG:
            text += 'L'
        elif self.internal_type is InternalType.DOUBLE:
            text += 'D'
        return self.inline_quoted(text)

    def into_string_lhs(self) -> str:
        """
        var foo = %var.player/bar%
        ^^^^^^^
        """
        raise NotImplementedError

    def into_string_rhs(self, *, include_internal_type: bool = True) -> str:
        """
        var foo = %var.player/bar%
                  ^^^^^^^^^^^^^^^^
        """
        raise NotImplementedError

    def into_inside_string(self, include_fallback_value: bool = True) -> str:
        """
        chat "hello %player.name%"
                    ^^^^^^^^^^^^^
        """
        raise NotImplementedError

    @abstractmethod
    def equals_raw(self, other: object) -> bool:
        raise NotImplementedError

    @final
    def equals(
        self,
        other: object,
    ) -> bool:
        if not isinstance(other, Checkable):
            return False
        if self.internal_type is not other.internal_type:
            return False
        if self.fallback_value != other.fallback_value:
            return False
        return self.equals_raw(other)

    def __str__(self) -> str:
        return self.into_inside_string()

    @abstractmethod
    def cloned_raw(self) -> Self:
        raise NotImplementedError

    @final
    def cloned(self) -> Self:
        clone = self.cloned_raw()
        clone.internal_type = self.internal_type
        clone.fallback_value = self.fallback_value
        return clone

    def as_type(self, internal_type: InternalType, /) -> Self:
        """
        Creates a copy of the current object, with the internal type set to the specified type.
        """
        clone = self.cloned()
        clone.internal_type = internal_type
        if clone.fallback_value is not None:
            clone.fallback_value = internal_type.type_compatible_housing_type(
                clone.fallback_value,
            )
        return clone

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
        clone = self.cloned()
        clone.fallback_value = self.internal_type.type_compatible_housing_type(
            fallback_value,
        )
        if clone.internal_type is InternalType.ANY:
            clone.internal_type = InternalType.from_value(fallback_value)
        return clone

    def get_formatted_fallback_value(self) -> str | None:
        value = self.fallback_value or self.internal_type.default_housing_type()
        return housing_type_as_rhs(value) if value is not None else None

    def __add__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            self,
            other,
            BinaryOperator.Increment,
        )

    def __radd__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            other,
            self,
            BinaryOperator.Increment,
        )

    def __sub__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            self,
            other,
            BinaryOperator.Decrement,
        )

    def __rsub__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            other,
            self,
            BinaryOperator.Decrement,
        )

    def __mul__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            self,
            other,
            BinaryOperator.Multiply,
        )

    def __rmul__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            other,
            self,
            BinaryOperator.Multiply,
        )

    def __truediv__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        if self.internal_type is InternalType.LONG:
            warn(
                'Dividing a LONG value will act as a floor division, consider using a floor division operator (//) instead',
            )

        return BinaryExpression(
            self,
            other,
            BinaryOperator.Divide,
        )

    def __rtruediv__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        if self.internal_type is InternalType.LONG:
            warn(
                'Dividing a LONG value will act as a floor division, consider using a floor division operator (//) instead',
            )

        return BinaryExpression(
            other,
            self,
            BinaryOperator.Divide,
        )

    def __floordiv__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        if self.internal_type is InternalType.DOUBLE:
            warn(
                'Floor dividing a DOUBLE value will act as a true division, consider using a true division operator (/) instead',
            )

        return BinaryExpression(
            self,
            other,
            BinaryOperator.Divide,
        )

    def __rfloordiv__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        if self.internal_type is InternalType.DOUBLE:
            warn(
                'Floor dividing a DOUBLE value will act as a true division, consider using a true division operator (/) instead',
            )

        return BinaryExpression(
            other,
            self,
            BinaryOperator.Divide,
        )

    @overload
    def __pow__(
        self,
        other: Literal[0],
    ) -> Literal[1]: ...

    @overload
    def __pow__(
        self,
        other: Literal[1],
    ) -> Self: ...

    @overload
    def __pow__(
        self,
        other: int,
    ) -> 'CompoundExpression | Self | Literal[1]': ...

    def __pow__(
        self,
        other: int,
    ) -> 'CompoundExpression | Self | Literal[1]':
        if other < 0:
            raise ValueError('Exponent must be a non-negative integer')
        if other == 0:
            return 1
        if other == 1:
            return self

        from .expression.binary_expression import BinaryExpression, BinaryOperator
        from .expression.compound_expression import CompoundExpression
        from .expression.expression import Expression
        from .stats.temporary_stat import TemporaryStat

        tmp = TemporaryStat(self.internal_type)

        def build_ops(n: int) -> list[Expression]:
            if n == 1:
                return []
            if n % 2 == 0:
                return build_ops(n // 2) + [
                    BinaryExpression(tmp, tmp, BinaryOperator.Multiply),
                ]
            # odd: try both approaches, pick the shorter one
            # option a: x^((n-1)/2) -> square -> multiply by x
            option_a = build_ops((n - 1) // 2) + [
                BinaryExpression(tmp, tmp, BinaryOperator.Multiply),
                BinaryExpression(tmp, self, BinaryOperator.Multiply),
            ]
            # option b: x^((n+1)/2) -> square -> divide by x
            option_b = build_ops((n + 1) // 2) + [
                BinaryExpression(tmp, tmp, BinaryOperator.Multiply),
                BinaryExpression(tmp, self, BinaryOperator.Divide),
            ]
            return option_a if len(option_a) <= len(option_b) else option_b

        expressions: list[Expression] = [
            BinaryExpression(tmp, self, BinaryOperator.Set),
        ]
        expressions.extend(build_ops(other))
        return CompoundExpression(expressions, tmp)

    def remainder(
        self,
        other: 'Checkable | NumericHousingType',
    ) -> 'CompoundExpression':
        from .expression.binary_expression import BinaryExpression, BinaryOperator
        from .expression.compound_expression import (
            CompoundExpression,
        )
        from .expression.expression import Expression
        from .stats.temporary_stat import TemporaryStat

        expressions: list[Expression] = []

        temporary_stat_1 = TemporaryStat(self.internal_type)
        expressions.append(
            BinaryExpression(
                left=temporary_stat_1,
                right=self,
                operator=BinaryOperator.Set,
            ),
        )
        expressions.append(
            BinaryExpression(
                left=temporary_stat_1,
                right=other,
                operator=BinaryOperator.Divide,
            ),
        )
        if self.internal_type is InternalType.DOUBLE:
            expressions.append(
                BinaryExpression(
                    left=temporary_stat_1.as_long(),
                    right=temporary_stat_1,
                    operator=BinaryOperator.Set,
                    is_intentional_self_assignment=True,
                ),
            )
            expressions.append(
                BinaryExpression(
                    left=temporary_stat_1.as_double(),
                    right=temporary_stat_1,
                    operator=BinaryOperator.Set,
                    is_intentional_self_assignment=True,
                ),
            )
        expressions.append(
            BinaryExpression(
                left=temporary_stat_1,
                right=other,
                operator=BinaryOperator.Multiply,
            ),
        )

        temporary_stat_2 = TemporaryStat(self.internal_type)
        expressions.append(
            BinaryExpression(
                left=temporary_stat_2,
                right=self,
                operator=BinaryOperator.Set,
            ),
        )
        expressions.append(
            BinaryExpression(
                left=temporary_stat_2,
                right=temporary_stat_1,
                operator=BinaryOperator.Decrement,
            ),
        )

        return CompoundExpression(expressions, temporary_stat_2)

    def __mod__(
        self,
        other: 'Checkable | NumericHousingType',
    ) -> 'CompoundExpression':
        from .expression.binary_expression import BinaryExpression, BinaryOperator
        from .expression.compound_expression import CompoundExpression
        from .expression.condition.comparison_condition import (
            ComparisonCondition,
            ComparisonOperator,
        )
        from .expression.condition.conditional_expression import (
            ConditionalExpression,
            ConditionalMode,
        )
        from .expression.expression import Expression

        remainder = self.remainder(other)
        result = remainder.result

        expressions: list[Expression] = list(remainder.expressions)
        expressions.append(
            ConditionalExpression(
                conditions=[
                    ComparisonCondition(
                        left=result,
                        right=0,
                        operator=ComparisonOperator.LessThan,
                    ),
                ],
                mode=ConditionalMode.AND,
                if_expressions=[
                    BinaryExpression(
                        left=result,
                        right=other,
                        operator=BinaryOperator.Increment,
                    ),
                ],
            ),
        )

        return CompoundExpression(expressions, result)

    def __and__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            self,
            other,
            BinaryOperator.BitwiseAnd,
        )

    def __rand__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            other,
            self,
            BinaryOperator.BitwiseAnd,
        )

    def __or__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            self,
            other,
            BinaryOperator.BitwiseOr,
        )

    def __ror__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            other,
            self,
            BinaryOperator.BitwiseOr,
        )

    def __xor__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            self,
            other,
            BinaryOperator.BitwiseXor,
        )

    def __rxor__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            other,
            self,
            BinaryOperator.BitwiseXor,
        )

    def __lshift__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            self,
            other,
            BinaryOperator.LeftShift,
        )

    def __rlshift__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            other,
            self,
            BinaryOperator.LeftShift,
        )

    def __rshift__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            self,
            other,
            BinaryOperator.RightShift,
        )

    def __rrshift__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            other,
            self,
            BinaryOperator.RightShift,
        )

    def logical_rshift[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        from .expression.binary_expression import BinaryExpression, BinaryOperator

        return BinaryExpression(
            self,
            other,
            BinaryOperator.LogicalRightShift,
        )

    def __neg__(self) -> 'BinaryExpression[Self, Literal[-1]]':
        return self.__mul__(-1)

    def abs(self) -> 'CompoundExpression':
        raise NotImplementedError  # TODO

    def __abs__(self) -> 'CompoundExpression':
        return self.abs()

    def __eq__[T: 'Checkable | HousingType'](
        self,
        other: T,
    ) -> ComparisonCondition[Self, T]:
        return ComparisonCondition(
            self,
            other,
            ComparisonOperator.Equal,
        )

    def __ne__[T: 'Checkable | HousingType'](
        self,
        other: T,
    ) -> ComparisonCondition[Self, T]:
        return ~self.__eq__(other)

    def __gt__[T: 'Checkable | HousingType'](
        self,
        other: T,
    ) -> ComparisonCondition[Self, T]:
        return ComparisonCondition(
            self,
            other,
            ComparisonOperator.GreaterThan,
        )

    def __lt__[T: 'Checkable | HousingType'](
        self,
        other: T,
    ) -> ComparisonCondition[Self, T]:
        return ComparisonCondition(
            self,
            other,
            ComparisonOperator.LessThan,
        )

    def __ge__[T: 'Checkable | HousingType'](
        self,
        other: T,
    ) -> ComparisonCondition[Self, T]:
        return ComparisonCondition(
            self,
            other,
            ComparisonOperator.GreaterThanOrEqual,
        )

    def __le__[T: 'Checkable | HousingType'](
        self,
        other: T,
    ) -> ComparisonCondition[Self, T]:
        return ComparisonCondition(
            self,
            other,
            ComparisonOperator.LessThanOrEqual,
        )

    @property
    def value(self) -> Self:
        clone = self.cloned()
        return clone

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError
