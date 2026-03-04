from collections.abc import Generator
from enum import Enum
from typing import Any, Self, final

from ..checkable import Checkable
from ..editable import Editable
from ..internal_type import InternalType
from ..stats.stat import Stat
from ..stats.temporary_stat import TemporaryStat
from .expression import Expression
from .housing_type import HousingType, housing_type_as_right_side

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
    is_intentional_self_assignment: bool

    def __init__(
        self,
        left: LeftT,
        right: RightT,
        operator: BinaryOperator,
        *,
        allow_self_assignment: bool = False,
    ) -> None:
        super().__init__(internal_type=InternalType.from_value(left))
        self.left = left
        self.right = right
        self.operator = operator
        self.is_intentional_self_assignment = allow_self_assignment

        if self.is_intentional_self_assignment and (
            not isinstance(self.left, Stat)
            or not self.left.is_same_stat(self.right)
            or operator is not BinaryOperator.Set
        ):
            raise ValueError(
                'Self assignment is only allowed for the same stat on both sides, with the Set operator'
            )

    def walk_expressions(self) -> Generator[Expression, None, None]:
        yield from super().walk_expressions()
        if isinstance(self.left, BinaryExpression):
            yield from self.left.walk_expressions()
        if isinstance(self.right, BinaryExpression):
            yield from self.right.walk_expressions()

    def into_assignment_expression(self) -> AssignmentExpression:
        if not isinstance(self.left, Editable):
            raise TypeError('Left side of a binary expression must be editable')
        if not isinstance(self.right, Checkable | HousingType):
            raise TypeError(
                'Right side of a binary expression must be checkable or a housing type'
            )
        return self  # type: ignore

    def generate_assignment_expressions(self) -> list[AssignmentExpression]:
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

        for expr in assignment_expressions:
            expr.right = expr.left.internal_type.type_compatible(expr.right)

        return assignment_expressions

    @staticmethod
    def take_out_useless_expressions(expressions: list[Expression]) -> None:
        for i in range(len(expressions) - 1, -1, -1):
            _expression = expressions[i]

            if not isinstance(_expression, BinaryExpression):
                continue
            expression = _expression.into_assignment_expression()

            if (
                isinstance(expression.left, Stat)
                and expression.left.is_same_stat(expression.right)
                and expression.operator is BinaryOperator.Set
                and not expression.is_intentional_self_assignment
            ):
                # stat = stat
                del expressions[i]

            elif (
                (
                    expression.operator is BinaryOperator.Increment
                    or expression.operator is BinaryOperator.Decrement
                )
                and isinstance(expression.right, int | float)
                and (expression.right == 0 or expression.right == 0.0)
            ):
                # editable += 0
                # editable -= 0
                del expressions[i]

            elif (
                (
                    expression.operator is BinaryOperator.Multiply
                    or expression.operator is BinaryOperator.Divide
                )
                and isinstance(expression.right, int | float)
                and (expression.right == 1 or expression.right == 1.0)
            ):
                # editable *= 1
                # editable /= 1
                del expressions[i]

    @staticmethod
    def rename_temporary_stats(expressions: list[Expression]) -> None:
        temp_stats: dict[int, list[TemporaryStat]] = {}
        for expression in expressions:
            for expr in expression.walk_expressions():
                for stat in expr.get_all_stats_used().values():
                    if not isinstance(stat, TemporaryStat):
                        continue
                    temp_stats.setdefault(stat.number, []).append(stat)

        for new_number, stats in enumerate(temp_stats.values(), start=1):
            for stat in stats:
                stat.number = new_number

    @staticmethod
    def optimize_binary_expressions(expressions: list[Expression]) -> None:
        has_changed = True
        while has_changed:
            has_changed = False

            for i, _expression in enumerate(expressions):
                if not isinstance(_expression, BinaryExpression):
                    continue
                expression = _expression.into_assignment_expression()

                if not isinstance(expression.left, Stat):
                    continue
                if not isinstance(expression.right, TemporaryStat):
                    continue
                if expression.operator is not BinaryOperator.Set:
                    continue

                # We have:
                # `left = right` (left is a stat, right is a temp stat)
                # this means that
                #     - we can replace all previous right with left
                #     - but ONLY IF
                #         * left is not used before this line together with right
                #             the exception being `right = left`
                #         * right is not used after this line

                def left_and_right_used_together_with_exception(
                    expr: Expression,
                    left: Stat,
                    right: TemporaryStat,
                ) -> bool:
                    if not expr.is_using_stats_together(left, right):
                        return False

                    # This would only get ran if `left = right`
                    # The exception is: `right = left`, then this is still False
                    if isinstance(expr, BinaryExpression):
                        if (
                            expr.operator is BinaryOperator.Set
                            and left.is_same_stat(expr.right)
                            and right.is_same_stat(expr.left)
                        ):
                            return False

                    return True

                if any(
                    left_and_right_used_together_with_exception(
                        expressions[j],
                        expression.left,
                        expression.right,
                    )
                    for j in range(i - 1, -1, -1)
                ):
                    continue

                if any(
                    expressions[j].is_using_stat(expression.right)
                    for j in range(i + 1, len(expressions))
                ):
                    continue

                has_changed |= any(
                    expressions[j].change_all_occurrences_of_stat(
                        expression.right, expression.left
                    )
                    for j in range(i + 1)
                )

        BinaryExpression.take_out_useless_expressions(expressions)
        BinaryExpression.rename_temporary_stats(expressions)

    def into_executable_expressions(self) -> Generator[Expression, None, None]:
        expressions = self.generate_assignment_expressions()
        self.optimize_binary_expressions(expressions)  # pyright: ignore[reportArgumentType]
        yield from expressions

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

        return '\n'.join(map(into_line, self.into_executable_expressions()))  # type: ignore

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
