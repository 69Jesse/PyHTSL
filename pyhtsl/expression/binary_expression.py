from collections.abc import Generator
from enum import Enum
from functools import cached_property
from typing import Any, NoReturn, Self, final

import numpy as np

from ..checkable import Checkable
from ..editable import Editable
from ..execute.backend_type import (
    backend_to_default_backend,
    is_default_backend,
)
from ..execute.context import ExecutionContext
from ..execute.exception import (
    MismatchedTypeException,
    NotANumberException,
    descriptive_backend_type,
)
from ..internal_type import InternalType
from ..logger import log
from ..stats.stat import Stat
from ..stats.temporary_stat import Number, TemporaryStat
from .compound_expression import CompoundExpression
from .condition.comparison_condition import ComparisonCondition
from .expression import Expression
from .housing_type import HousingType, housing_type_as_rhs

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
    BitwiseAnd = '&='
    BitwiseOr = '|='
    BitwiseXor = '^='
    LeftShift = '<<='
    RightShift = '>>='
    LogicalRightShift = '>>>='

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}, {self.value}>'

    @cached_property
    def allowed_types(self) -> set[InternalType]:
        if self is BinaryOperator.Set:
            return InternalType.all_types()
        else:
            return InternalType.numeric_types()


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
        is_intentional_self_assignment: bool = False,
    ) -> None:
        super().__init__(internal_type=InternalType.from_value(left))
        self.left = left
        self.right = right
        self.operator = operator
        self.is_intentional_self_assignment = is_intentional_self_assignment

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

    def is_assignment_expression(self) -> bool:
        try:
            self.into_assignment_expression()
            return True
        except TypeError:
            return False

    @staticmethod
    def fix_type_compatibility(
        binary_object: AssignmentExpression | ComparisonCondition,
    ) -> None:
        if (
            isinstance(binary_object, BinaryExpression)
            and binary_object.is_intentional_self_assignment
        ):
            return

        def raise_type_error(
            side: str,
            value: Checkable | HousingType,
            actual: InternalType,
            allowed: set[InternalType],
        ) -> NoReturn:
            raise TypeError(
                f'{side} side of operator "{binary_object.operator.name}" ({value!r}) must be one of the following types: '
                f'{", ".join(t.name for t in sorted(allowed, key=lambda t: t.value))}. Got {actual.name}.'
            )

        if (
            binary_object.left.internal_type is not InternalType.ANY
            and binary_object.left.internal_type
            not in binary_object.operator.allowed_types
        ):
            raise_type_error(
                'Left',
                binary_object.left,
                binary_object.left.internal_type,
                binary_object.operator.allowed_types,
            )

        binary_object.right = binary_object.left.internal_type.type_compatible(
            binary_object.right
        )

        right_internal_type = InternalType.from_value(binary_object.right)
        if (
            right_internal_type is not InternalType.ANY
            and right_internal_type not in binary_object.operator.allowed_types
        ):
            raise_type_error(
                'Right',
                binary_object.right,
                right_internal_type,
                binary_object.operator.allowed_types,
            )

    def flatten(self) -> list[Expression]:
        expressions: list[Expression] = []

        def minimize(
            expr: BinaryExpression[Any, Any] | Checkable | HousingType,
        ) -> Checkable | HousingType:
            if isinstance(expr, CompoundExpression):
                expressions.extend(e.cloned() for e in expr.expressions)
                return expr.result.cloned()

            if not isinstance(expr, BinaryExpression):
                return expr

            left: Checkable | HousingType = (
                minimize(expr.left)
                if isinstance(expr.left, BinaryExpression)
                else expr.left
            )
            right: Checkable | HousingType = (
                minimize(expr.right)
                if isinstance(expr.right, BinaryExpression)
                else expr.right
            )

            internal_type = InternalType.from_value(left)
            stat = TemporaryStat(internal_type)
            expressions.append(
                BinaryExpression(
                    left=stat,
                    right=left,
                    operator=BinaryOperator.Set,
                )
            )
            expressions.append(
                BinaryExpression(
                    left=stat,
                    right=right,
                    operator=expr.operator,
                    is_intentional_self_assignment=expr.is_intentional_self_assignment,
                )
            )
            return stat

        left = minimize(self.left)
        assert isinstance(left, Editable)
        right = minimize(self.right)

        expressions.append(
            BinaryExpression(
                left=left,
                right=right,
                operator=self.operator,
                is_intentional_self_assignment=self.is_intentional_self_assignment,
            ),
        )

        for expr in expressions:
            if isinstance(expr, BinaryExpression) and expr.is_assignment_expression():
                BinaryExpression.fix_type_compatibility(
                    expr.into_assignment_expression()
                )

        return expressions

    @staticmethod
    def take_out_useless_expressions(expressions: list[Expression]) -> None:
        has_changed = True
        while has_changed:
            has_changed = False
            has_changed |= BinaryExpression._remove_no_op_expressions(expressions)
            has_changed |= BinaryExpression._merge_identity_set_with_op(expressions)
            has_changed |= BinaryExpression._fold_consecutive_constant_ops(expressions)
            has_changed |= BinaryExpression._eliminate_dead_stores(expressions)

    @staticmethod
    def _remove_no_op_expressions(expressions: list[Expression]) -> bool:
        has_changed = False
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
                has_changed = True

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
                has_changed = True

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
                has_changed = True

            elif (
                (
                    expression.operator is BinaryOperator.BitwiseOr
                    or expression.operator is BinaryOperator.BitwiseXor
                    or expression.operator is BinaryOperator.LeftShift
                    or expression.operator is BinaryOperator.RightShift
                    or expression.operator is BinaryOperator.LogicalRightShift
                )
                and isinstance(expression.right, int)
                and expression.right == 0
            ):
                # editable |= 0
                # editable ^= 0
                # editable <<= 0
                # editable >>= 0
                # editable >>>= 0
                del expressions[i]
                has_changed = True

        return has_changed

    @staticmethod
    def _is_left_identity_for(operator: BinaryOperator, value: object) -> bool:
        """`identity OP rhs == rhs` lets us collapse `lhs = identity; lhs OP rhs`."""
        if operator is BinaryOperator.Increment and isinstance(value, int | float):
            return value == 0
        if operator is BinaryOperator.Multiply and isinstance(value, int | float):
            return value == 1
        if operator is BinaryOperator.BitwiseOr and isinstance(value, int):
            return value == 0
        if operator is BinaryOperator.BitwiseXor and isinstance(value, int):
            return value == 0
        if operator is BinaryOperator.BitwiseAnd and isinstance(value, int):
            return value == -1
        return False

    @staticmethod
    def _merge_identity_set_with_op(expressions: list[Expression]) -> bool:
        """`lhs = identity; lhs OP rhs` -> `lhs = rhs` (covers +, *, |, ^, &)."""
        has_changed = False
        i = 0
        while i < len(expressions) - 1:
            expr_i = expressions[i]
            if not (
                isinstance(expr_i, BinaryExpression)
                and isinstance(expr_i.left, Stat)
                and expr_i.operator is BinaryOperator.Set
                and not expr_i.is_intentional_self_assignment
            ):
                i += 1
                continue

            lhs = expr_i.left
            init_value = expr_i.right

            j = i + 1
            merge_target: BinaryExpression[Any, Any] | None = None
            while j < len(expressions):
                expr_j = expressions[j]
                if (
                    isinstance(expr_j, BinaryExpression)
                    and isinstance(expr_j.left, Stat)
                    and expr_j.left.is_same_stat(lhs)
                    and BinaryExpression._is_left_identity_for(
                        expr_j.operator, init_value
                    )
                ):
                    merge_target = expr_j
                    break
                if expr_j.is_using_stat(lhs):
                    break
                j += 1

            if merge_target is None:
                i += 1
                continue

            rhs = merge_target.right
            if isinstance(rhs, Stat):
                if rhs.is_same_stat(lhs):
                    i += 1
                    continue
                if any(
                    isinstance(expressions[k], BinaryExpression)
                    and isinstance(expressions[k].left, Stat)  # type: ignore[union-attr]
                    and expressions[k].left.is_same_stat(rhs)  # type: ignore[union-attr]
                    for k in range(i + 1, j)
                ):
                    i += 1
                    continue

            expressions[i] = BinaryExpression(
                left=lhs,
                right=rhs,
                operator=BinaryOperator.Set,
            )
            del expressions[j]
            has_changed = True
            i += 1

        return has_changed

    @staticmethod
    def _combine_constant_ops(
        op_a: BinaryOperator,
        val_a: int | float,
        op_b: BinaryOperator,
        val_b: int | float,
    ) -> tuple[BinaryOperator, int | float] | None:
        """Combine two consecutive constant ops on the same lhs into one."""
        # `lhs = c1; lhs OP c2` -> `lhs = applied(c1, c2)`. Skip Divide because
        # the result depends on lhs's internal type (long floors, double doesn't).
        if op_a is BinaryOperator.Set:
            if op_b is BinaryOperator.Increment:
                return BinaryOperator.Set, val_a + val_b
            if op_b is BinaryOperator.Decrement:
                return BinaryOperator.Set, val_a - val_b
            if op_b is BinaryOperator.Multiply:
                return BinaryOperator.Set, val_a * val_b
            if isinstance(val_a, int) and isinstance(val_b, int):
                if op_b is BinaryOperator.BitwiseAnd:
                    return BinaryOperator.Set, val_a & val_b
                if op_b is BinaryOperator.BitwiseOr:
                    return BinaryOperator.Set, val_a | val_b
                if op_b is BinaryOperator.BitwiseXor:
                    return BinaryOperator.Set, val_a ^ val_b
                if op_b is BinaryOperator.LeftShift:
                    return BinaryOperator.Set, val_a << val_b
                if op_b is BinaryOperator.RightShift:
                    return BinaryOperator.Set, val_a >> val_b
            return None

        # Inc/Dec mix arithmetically.
        if op_a in (BinaryOperator.Increment, BinaryOperator.Decrement) and op_b in (
            BinaryOperator.Increment,
            BinaryOperator.Decrement,
        ):
            sign_a = 1 if op_a is BinaryOperator.Increment else -1
            sign_b = 1 if op_b is BinaryOperator.Increment else -1
            combined = sign_a * val_a + sign_b * val_b
            if combined >= 0:
                return BinaryOperator.Increment, combined
            return BinaryOperator.Decrement, -combined

        if op_a is op_b:
            if op_a is BinaryOperator.Multiply:
                return op_a, val_a * val_b
            if op_a is BinaryOperator.Divide:
                return op_a, val_a * val_b
            if (
                op_a
                in (
                    BinaryOperator.LeftShift,
                    BinaryOperator.RightShift,
                    BinaryOperator.LogicalRightShift,
                )
                and isinstance(val_a, int)
                and isinstance(val_b, int)
            ):
                return op_a, val_a + val_b
            if isinstance(val_a, int) and isinstance(val_b, int):
                if op_a is BinaryOperator.BitwiseAnd:
                    return op_a, val_a & val_b
                if op_a is BinaryOperator.BitwiseOr:
                    return op_a, val_a | val_b
                if op_a is BinaryOperator.BitwiseXor:
                    return op_a, val_a ^ val_b

        return None

    @staticmethod
    def _fold_consecutive_constant_ops(expressions: list[Expression]) -> bool:
        """`lhs OP1 c1; lhs OP2 c2` -> `lhs OP_combined c_combined` when adjacent."""
        has_changed = False
        i = 0
        while i < len(expressions) - 1:
            expr_a = expressions[i]
            expr_b = expressions[i + 1]
            if not (
                isinstance(expr_a, BinaryExpression)
                and isinstance(expr_b, BinaryExpression)
                and isinstance(expr_a.left, Stat)
                and isinstance(expr_b.left, Stat)
                and expr_a.left.is_same_stat(expr_b.left)
                and isinstance(expr_a.right, int | float)
                and isinstance(expr_b.right, int | float)
            ):
                i += 1
                continue

            combined = BinaryExpression._combine_constant_ops(
                expr_a.operator, expr_a.right, expr_b.operator, expr_b.right
            )
            if combined is None:
                i += 1
                continue

            new_op, new_val = combined
            expressions[i] = BinaryExpression(
                left=expr_a.left,
                right=new_val,
                operator=new_op,
            )
            del expressions[i + 1]
            has_changed = True
            # Don't advance; the new expression at i may fold with i+1.

        return has_changed

    @staticmethod
    def _eliminate_dead_stores(expressions: list[Expression]) -> bool:
        """`lhs OP a; ... (lhs unread) ...; lhs = b` (b doesn't read lhs) -> drop first.

        Any op that writes to lhs (Set, Increment, Multiply, ...) is dead if the
        next expression that touches lhs is a full overwrite without reading it.
        """
        has_changed = False
        i = 0
        while i < len(expressions):
            expr_i = expressions[i]
            if not (
                isinstance(expr_i, BinaryExpression)
                and isinstance(expr_i.left, Stat)
                and not expr_i.is_intentional_self_assignment
            ):
                i += 1
                continue

            lhs = expr_i.left
            is_dead = False
            for j in range(i + 1, len(expressions)):
                expr_j = expressions[j]
                if not expr_j.is_using_stat(lhs):
                    continue
                if (
                    isinstance(expr_j, BinaryExpression)
                    and isinstance(expr_j.left, Stat)
                    and expr_j.left.is_same_stat(lhs)
                    and expr_j.operator is BinaryOperator.Set
                    and not expr_j.is_intentional_self_assignment
                    and not (
                        isinstance(expr_j.right, Stat)
                        and expr_j.right.is_same_stat(lhs)
                    )
                ):
                    is_dead = True
                break

            if is_dead:
                del expressions[i]
                has_changed = True
            else:
                i += 1

        return has_changed

    @staticmethod
    def rename_temporary_stats(expressions: list[Expression]) -> None:
        reserved: set[int] = set()
        first_uses: list[TemporaryStat] = []
        seen: set[Number] = set()
        for expression in expressions:
            for expr in expression.walk_expressions():
                for stat, _ in expr.get_all_stats_used():
                    if isinstance(stat, TemporaryStat):
                        if stat._number not in seen:
                            seen.add(stat._number)
                            first_uses.append(stat)
                    else:
                        n = TemporaryStat.extract_number_from_name(stat.name)
                        if n is not None:
                            reserved.add(n)

        next_number = 0
        for stat in first_uses:
            while next_number in reserved:
                next_number += 1
            reserved.add(next_number)
            stat.number = next_number
            next_number += 1

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
                if expression.left.is_same_stat(expression.right):
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

    def into_executable_expressions(self) -> Generator[Expression, None, None]:
        expressions = self.flatten()
        self.optimize_binary_expressions(expressions)
        self.rename_temporary_stats(expressions)
        yield from expressions

    def create_temp_stat_and_write(self) -> TemporaryStat:
        stat = TemporaryStat(self.internal_type)

        expressions = list(
            BinaryExpression(
                left=stat,
                right=self,
                operator=BinaryOperator.Set,
            ).into_executable_expressions()
        )
        for expr in expressions:
            expr.write()

        return stat

    def into_string_lhs(self) -> str:
        return self.create_temp_stat_and_write().into_string_lhs()

    def into_string_rhs(self, *, include_internal_type: bool = True) -> str:
        return self.create_temp_stat_and_write().into_string_rhs(
            include_internal_type=include_internal_type,
        )

    def into_inside_string(self, include_fallback_value: bool = True) -> str:
        return self.create_temp_stat_and_write().into_inside_string(
            include_fallback_value=include_fallback_value,
        )

    def into_htsl(self) -> str:
        def format_rhs(value: Checkable | HousingType) -> str:
            if isinstance(value, Checkable):
                return value.into_string_rhs()
            return housing_type_as_rhs(value)

        def into_line(expr: Expression) -> str:
            if not isinstance(expr, BinaryExpression):
                return expr.into_htsl()

            line = f'{expr.left.into_string_lhs()} {expr.operator.value} {format_rhs(expr.right)}'

            if isinstance(expr.left, Stat):
                line += f' {str(expr.left.auto_unset).lower()}'

            return line

        return '\n'.join(map(into_line, self.into_executable_expressions()))

    def cloned_raw(self) -> Self:
        return self.__class__(
            left=self.cloned_or_same(self.left),
            right=self.cloned_or_same(self.right),
            operator=self.operator,
            is_intentional_self_assignment=self.is_intentional_self_assignment,
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

    @staticmethod
    def execute_assignment_expression(
        expression: AssignmentExpression,
        context: 'ExecutionContext',
    ) -> None:
        if expression.operator is BinaryOperator.Set:
            context.put(
                expression.left,
                context.get(expression.right, output='backend'),
                ignore_warning=True,
            )
            return

        right_identifier = (
            expression.right
            if not isinstance(expression.right, Checkable)
            else expression.right.into_string_rhs()
        )
        left_value = context.get(
            expression.left,
            default=backend_to_default_backend(
                context.get(
                    right_identifier,
                    output='backend',
                )
            ),
            output='backend',
        )
        right_value = context.get(
            right_identifier,
            default=backend_to_default_backend(left_value),
            output='backend',
        )

        if type(left_value) is not type(right_value):
            MismatchedTypeException.throw(
                left=(expression.left, left_value),
                right=(expression.right, right_value),
                operator=expression.operator,
            )

        # String operations are not supported
        if isinstance(left_value, str):
            NotANumberException.throw(
                left=(expression.left, left_value),
                right=(expression.right, right_value),
                operator=expression.operator,
            )

        if not isinstance(left_value, np.integer | np.floating) or not isinstance(
            right_value, np.integer | np.floating
        ):
            raise RuntimeError(
                'Expected numeric values for binary expression execution'
            )

        if expression.operator in (
            BinaryOperator.BitwiseAnd,
            BinaryOperator.BitwiseOr,
            BinaryOperator.BitwiseXor,
            BinaryOperator.LeftShift,
            BinaryOperator.RightShift,
            BinaryOperator.LogicalRightShift,
        ):
            # For logical operators, convert to longs
            left_long = np.int64(np.floor(left_value))
            right_long = np.int64(np.floor(right_value))

            if expression.operator is BinaryOperator.BitwiseAnd:
                result_long = left_long & right_long
            elif expression.operator is BinaryOperator.BitwiseOr:
                result_long = left_long | right_long
            elif expression.operator is BinaryOperator.BitwiseXor:
                result_long = left_long ^ right_long
            elif expression.operator is BinaryOperator.LeftShift:
                result_long = left_long << right_long
            elif expression.operator is BinaryOperator.RightShift:
                result_long = left_long >> right_long
            elif expression.operator is BinaryOperator.LogicalRightShift:
                # Logical right shift (unsigned)
                if left_long < 0:
                    result_long = (left_long % (1 << 64)) >> right_long
                else:
                    result_long = left_long >> right_long
            else:
                raise ValueError(f'Unexpected operator: {expression.operator}')

            # If original was double, convert back to double
            if isinstance(left_value, np.floating):
                result = np.float64(result_long)
            else:
                result = result_long

            context.put(expression.left, result, ignore_warning=True)
            return

        # Arithmetic operators
        if expression.operator is BinaryOperator.Increment:
            result = left_value + right_value
        elif expression.operator is BinaryOperator.Decrement:
            result = left_value - right_value
        elif expression.operator is BinaryOperator.Multiply:
            result = left_value * right_value
        elif expression.operator is BinaryOperator.Divide:
            if right_value == 0:
                return
            if isinstance(left_value, np.integer) and isinstance(
                right_value, np.integer
            ):
                result = left_value // right_value
            else:
                result = left_value / right_value
        else:
            raise ValueError(f'Unexpected operator: {expression.operator}')

        if isinstance(expression.left, Stat) and expression.left.auto_unset:
            if is_default_backend(result):
                context.pop(expression.left)
                return

        context.put(expression.left, result, ignore_warning=True)

    def raw_execute(self, context: 'ExecutionContext') -> None:
        for expr in self.into_executable_expressions():
            if not isinstance(expr, BinaryExpression):
                expr.execute(context)
                continue
            expr = expr.into_assignment_expression()
            if context.verbose:
                log(
                    f'{" " * 4}Executing \x1b[38;2;255;0;0m"{expr.left!r} {expr.operator.value} {expr.right!r}"\x1b[0m'
                )
                log(
                    f'{" " * 8}BEFORE: {expr.left.into_string_lhs()} = {descriptive_backend_type(context.get(expr.left, output="backend"))}'
                )
            self.execute_assignment_expression(expr, context)
            if context.verbose:
                log(
                    f'{" " * 8}AFTER:  {expr.left.into_string_lhs()} = {descriptive_backend_type(context.get(expr.left, output="backend"))}'
                )
