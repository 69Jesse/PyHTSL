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
    housing_type_as_right_side,
)
from .internal_type import InternalType

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
        if include_internal_type and not no_type_casting():
            if self.internal_type is InternalType.LONG:
                text += 'L'
            elif self.internal_type is InternalType.DOUBLE:
                text += 'D'
        return f'"{text.replace('"', '\\"')}"'

    def into_assignment_left_side(self) -> str:
        """
        var foo = %var.player/bar%
        ^^^^^^^
        """
        raise NotImplementedError

    def into_assignment_right_side(self, *, include_internal_type: bool = True) -> str:
        """
        var foo = %var.player/bar%
                  ^^^^^^^^^^^^^^^^
        """
        raise NotImplementedError

    def into_comparison_left_side(self) -> str:
        """
        if and (var "foo" > %var.player/bar%) {
                ^^^^^^^^^
        """
        raise NotImplementedError

    def into_comparison_right_side(self) -> str:
        """
        if and (var "foo" > %var.player/bar%) {
                            ^^^^^^^^^^^^^^^^
        """
        raise NotImplementedError

    def into_string(self, include_fallback_value: bool = True) -> str:
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
        return self.into_string()

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
        return housing_type_as_right_side(value) if value is not None else None

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

        return BinaryExpression(
            other,
            self,
            BinaryOperator.Divide,
        )

    def __floordiv__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[Self, T]':
        return self.__truediv__(other)

    def __rfloordiv__[T: 'Checkable | NumericHousingType'](
        self,
        other: T,
    ) -> 'BinaryExpression[T, Self]':
        return self.__rtruediv__(other)

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
        other: int,  # TODO type guard with >= 2 for only expression array
    ) -> 'CompoundExpression | Self | Literal[1]': ...

    def __pow__(
        self,
        other: int,
    ) -> 'CompoundExpression | Self | Literal[1]':
        raise NotImplementedError  # TODO

    def remainder(
        self,
        other: 'Checkable | NumericHousingType',
    ) -> 'CompoundExpression':
        raise NotImplementedError  # TODO

    def __mod__(
        self,
        other: 'Checkable | NumericHousingType',
    ) -> 'CompoundExpression':
        raise NotImplementedError  # TODO

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
