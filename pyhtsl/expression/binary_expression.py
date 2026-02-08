from ..internal_type import InternalType
from ..stats.temporary_stat import TemporaryStat
from ..checkable import Checkable
from ..editable import Editable
from .housing_type import HousingType, housing_type_as_right_side
from .expression import Expression
from ..stats.stat import Stat

from enum import Enum

from typing import Any, Self, final


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


type AssignmentExpression = BinaryExpression[Editable, Checkable | HousingType]


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
            or not isinstance(self.left, Stat)
            or not isinstance(self.right, Checkable)
            or not self.left.equals_raw(self.right)
            or operator is not BinaryOperator.Set
        ):
            pass

    def into_assignment_expressions(self) -> list[AssignmentExpression]:
        assignment_expressions: list[AssignmentExpression] = []

        def minimize(
            expr: BinaryExpression[Any, Any] | Checkable | HousingType,
        ) -> Checkable | HousingType:
            if not isinstance(expr, BinaryExpression):
                return expr

            if isinstance(expr.left, BinaryExpression):
                expr.left = minimize(expr.left)
            if isinstance(expr.right, BinaryExpression):
                expr.right = minimize(expr.right)

            assert not (
                isinstance(expr.left, HousingType) and isinstance(expr.left, Checkable)
            )

            internal_type = InternalType.from_value(expr.left)
            stat = TemporaryStat(internal_type)
            assignment_expressions.append(
                BinaryExpression(
                    left=stat,
                    right=expr.left,
                    operator=BinaryOperator.Set,
                )
            )
            assignment_expressions.append(
                BinaryExpression(
                    left=stat,
                    right=expr.right,
                    operator=expr.operator,
                )
            )
            return stat

        left = minimize(self.left)
        assert isinstance(left, Editable)
        right = minimize(self.right)

        assignment_expressions.append(
            BinaryExpression(
                left=left,
                right=right,
                operator=self.operator,
            ),
        )

        return assignment_expressions

    def into_htsl(self) -> str:
        def format_rhs(value: Checkable | HousingType) -> str:
            if isinstance(value, Checkable):
                return value.into_assignment_right_side()
            return housing_type_as_right_side(value)

        def into_line(expr: AssignmentExpression) -> str:
            line = f'{expr.left.into_assignment_left_side()} {expr.operator.value} {format_rhs(expr.right)}'

            if isinstance(expr.left, Stat):
                line += f' {str(expr.left.auto_unset).lower()}'

            return line

        return '\n'.join(map(into_line, self.into_assignment_expressions()))

    def cloned_raw(self) -> Self:
        return self.__class__(
            left=self.cloned_or_same(self.left),
            right=self.cloned_or_same(self.right),
            operator=self.operator,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, BinaryExpression):
            return False
        return (
            self.equals_or_eq(self.left, other.left)
            and self.equals_or_eq(self.right, other.right)
            and self.operator == other.operator
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{repr(self.left)} {self.operator.value} {repr(self.right)}>'
