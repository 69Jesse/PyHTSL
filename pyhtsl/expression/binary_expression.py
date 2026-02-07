from ..base_object import BaseObject
from ..checkable import Checkable
from ..editable import Editable
from .housing_type import HousingType, housing_type_as_right_side
from .expression import Expression
from ..stats.base_stat import BaseStat

from enum import Enum

from typing import Self, final


__all__ = (
    'BinaryOperator',
    'BinaryExpression',
)


class BinaryOperator(Enum):
    Set = '='
    Increment = '+='
    Decrement = '-='
    Multiply = '*='
    Divide = '/='

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}, {self.value}>'


@final
class BinaryExpression[
    LeftT: 'BinaryExpression | Checkable | HousingType',
    RightT: 'BinaryExpression | Checkable | HousingType',
](Expression, Editable):
    left: LeftT
    right: RightT
    operator: BinaryOperator
    allow_self_assignment: bool

    def __init__(
        self,
        left: LeftT,
        right: RightT,
        operator: BinaryOperator,
        *,
        allow_self_assignment: bool = False,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator
        self.allow_self_assignment = allow_self_assignment

        if (
            self.allow_self_assignment
            or not isinstance(self.left, BaseStat)
            or not self.left.equals_raw(self.right)
            or operator is not BinaryOperator.Set
        ):
            pass

    def into_assignment_expressions(
        self,
    ) -> list['BinaryExpression[Editable, Checkable | HousingType]']:
        return []  # TODO

    def into_htsl(self) -> str:
        def into_line(
            expr: 'BinaryExpression[Editable, Checkable | HousingType]',
        ) -> str:
            def format_rhs(value: Checkable | HousingType) -> str:
                if isinstance(value, Checkable):
                    return value.into_assignment_right_side()
                return housing_type_as_right_side(value)

            line = f'{expr.left.into_assignment_left_side()} {expr.operator.value} {format_rhs(expr.right)}'

            if isinstance(expr.left, BaseStat):
                line += f' {str(expr.left.auto_unset).lower()}'

            return line

        return '\n'.join(map(into_line, self.into_assignment_expressions()))

    def cloned_raw(self) -> Self:
        return self.__class__(
            left=(
                self.left.cloned() if isinstance(self.left, BaseObject) else self.left
            ),
            right=(
                self.right.cloned()
                if isinstance(self.right, BaseObject)
                else self.right
            ),
            operator=self.operator,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, BinaryExpression):
            return False
        return (
            (
                self.left.equals(other.left)
                if isinstance(self.left, BaseObject)
                and isinstance(other.left, BaseObject)
                else (self.left == other.left)
                if not isinstance(self.left, BaseObject)
                and not isinstance(other.left, BaseObject)
                else False
            )
            and (
                self.right.equals(other.right)
                if isinstance(self.right, BaseObject)
                and isinstance(other.right, BaseObject)
                else (self.right == other.right)
                if not isinstance(self.right, BaseObject)
                and not isinstance(other.right, BaseObject)
                else False
            )
            and self.operator == other.operator
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{repr(self.left)} {self.operator.value} {repr(self.right)}>'
