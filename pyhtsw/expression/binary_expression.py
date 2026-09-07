from collections.abc import Generator
from enum import Enum
from functools import cached_property
from typing import Any, NoReturn, Self, final

import numpy as np

from pyhtsw.checkable import Checkable
from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.compiler.registry import ActionMeta
from pyhtsw.directives.no_optimization import optimization_enabled
from pyhtsw.directives.no_type_casting import no_type_casting
from pyhtsw.directives.preserved import is_preserved
from pyhtsw.editable import Editable
from pyhtsw.execute import java_long
from pyhtsw.execute.backend_type import (
    BackendType,
    JavaLong,
    backend_to_default_backend,
    into_backend_type,
    is_default_backend,
)
from pyhtsw.execute.exception import (
    MismatchedTypeException,
    NotANumberException,
    descriptive_backend_type,
)
from pyhtsw.execute.house import EmulatedHouse
from pyhtsw.expression.compound_expression import CompoundExpression
from pyhtsw.expression.condition.comparison_condition import ComparisonCondition
from pyhtsw.expression.expression import Expression
from pyhtsw.expression.housing_type import (
    VALUE_MAX_LENGTH,
    HousingType,
    check_value_length,
    housing_type_as_rhs,
)
from pyhtsw.internal_type import InternalType
from pyhtsw.stats.stat import Stat
from pyhtsw.stats.temporary_stat import (
    Number,
    TemporaryStat,
    currently_reserved_temp_numbers,
)
from pyhtsw.utils.log import log

__all__ = (
    'BinaryOperator',
    'BinaryExpression',
    'SET_STRING_MAX_LENGTH',
)


SET_STRING_MAX_LENGTH = VALUE_MAX_LENGTH


# Below this many BinaryExpression candidates the quadratic peephole scans are
# cheaper than building the per-pass index; above it the index wins by orders of
# magnitude. The gate counts BinaryExpressions, not total expressions, so a block
# that is mostly conditionals (few assignments) keeps the cheap scan.
_OPT_INDEX_THRESHOLD = 128


def _should_use_index(expressions: list['Expression']) -> bool:
    if len(expressions) <= _OPT_INDEX_THRESHOLD:
        return False
    candidates = 0
    for expr in expressions:
        if type(expr) is BinaryExpression:
            candidates += 1
            if candidates > _OPT_INDEX_THRESHOLD:
                return True
    return False


def _is_single_placeholder(value: str) -> bool:
    return any(
        pattern.fullmatch(value) is not None
        for pattern, _ in Checkable.iter_pattern_factories()
    )


def _rhs_references_stat(rhs: object, stat: 'Stat') -> bool:
    if isinstance(rhs, Stat):
        return rhs.is_same_stat(stat)
    if isinstance(rhs, Expression):
        return rhs.is_using_stat(stat)
    if isinstance(rhs, str):
        for ref in Checkable.iter_in_string(rhs):
            if isinstance(ref, Stat) and ref.is_same_stat(stat):
                return True
    # Composite values (e.g. a fallback-chain read) expose the stats they
    # reference at runtime through `iter_referenced_stats`.
    iter_refs = getattr(rhs, 'iter_referenced_stats', None)
    if iter_refs is not None:
        return any(ref.is_same_stat(stat) for ref in iter_refs())
    return False


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
    htsw_meta = ActionMeta(
        htsw_name='CHANGE_VAR',
        limit=25,
    )

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
        super().__init__(
            internal_type=BinaryExpression._operand_result_type(left, right),
        )
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
                'Self assignment is only allowed for the same stat on both sides, with the Set operator',
            )

    @staticmethod
    def _operand_result_type(
        left: 'BinaryExpression | Checkable | HousingType',
        right: 'BinaryExpression | Checkable | HousingType',
    ) -> InternalType:
        left_type = InternalType.from_value(left)
        if isinstance(left, int | float) and not isinstance(right, int | float):
            right_type = InternalType.from_value(right)
            if right_type is not InternalType.ANY:
                return right_type
        return left_type

    def walk_expressions(self) -> Generator[Expression]:
        yield from super().walk_expressions()
        for side in (self.left, self.right):
            if isinstance(side, BinaryExpression | CompoundExpression):
                yield from side.walk_expressions()

    def into_assignment_expression(self) -> AssignmentExpression:
        if not isinstance(self.left, Editable):
            raise TypeError('Left side of a binary expression must be editable')
        if not isinstance(self.right, Checkable | HousingType):
            raise TypeError(
                'Right side of a binary expression must be checkable or a housing type',
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
                f'{", ".join(t.name for t in sorted(allowed, key=lambda t: t.value))}. Got {actual.name}.',
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
            binary_object.right,
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
                for sub in expr.expressions:
                    sub = sub.cloned()
                    if isinstance(sub, BinaryExpression):
                        expressions.extend(sub.flatten())
                    else:
                        expressions.append(sub)
                return expr.result.cloned()

            if not isinstance(expr, BinaryExpression):
                return expr

            left: Checkable | HousingType = minimize(expr.left)
            right: Checkable | HousingType = minimize(expr.right)

            internal_type = BinaryExpression._operand_result_type(left, right)
            stat = TemporaryStat.transient()._as_type(internal_type)
            expressions.append(
                BinaryExpression(
                    left=stat,
                    right=left,
                    operator=BinaryOperator.Set,
                ),
            )
            expressions.append(
                BinaryExpression(
                    left=stat,
                    right=right,
                    operator=expr.operator,
                    is_intentional_self_assignment=expr.is_intentional_self_assignment,
                ),
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
                    expr.into_assignment_expression(),
                )

        return expressions

    @staticmethod
    def take_out_useless_expressions(expressions: list[Expression]) -> bool:
        """Run the peephole passes to a fixed point, returning whether anything changed."""
        no_ops = optimization_enabled('no_ops')
        # The merge/fold/dead-store passes need at least two expressions; for the
        # many empty/one-line conditional bodies finalize produces, only the
        # single-expression no-op removal can apply, so run just that.
        if len(expressions) < 2:
            return no_ops and BinaryExpression._remove_no_op_expressions(expressions)
        identity_merge = optimization_enabled('identity_merge')
        fold = optimization_enabled('fold')
        dead_stores = optimization_enabled('dead_stores')
        changed_any = False
        has_changed = True
        while has_changed:
            has_changed = False
            if no_ops:
                has_changed |= BinaryExpression._remove_no_op_expressions(expressions)
            if identity_merge:
                has_changed |= BinaryExpression._merge_identity_set_with_op(expressions)
            if fold:
                has_changed |= BinaryExpression._fold_consecutive_constant_ops(
                    expressions,
                )
            if dead_stores:
                has_changed |= BinaryExpression._eliminate_dead_stores(expressions)
            changed_any |= has_changed
        return changed_any

    @staticmethod
    def _is_execution_barrier(expression: Expression) -> bool:
        return any(
            type(expr).htsw_meta.control for expr in expression.walk_expressions()
        )

    @staticmethod
    def _stat_query_keys(stat: Stat) -> tuple[tuple, tuple]:
        direct = (type(stat), stat.name)
        if isinstance(stat, TemporaryStat):
            player = stat.into_player_stat()
            return direct, (type(player), player.name)
        return direct, direct

    @staticmethod
    def _expr_used_keys(expression: Expression) -> tuple[set, set]:
        direct: set = set()
        string: set = set()
        for expr in expression.walk_expressions():
            for s, _ in expr.get_all_stats_used():
                direct.add((type(s), s.name))
            for value in expr._get_all_values().values():
                iter_refs = getattr(value, 'iter_referenced_stats', None)
                if iter_refs is not None:
                    for ref in iter_refs():
                        direct.add((type(ref), ref.name))
                if not isinstance(value, str):
                    continue
                for ref in Checkable.iter_in_string(value):
                    if isinstance(ref, Stat):
                        string.add((type(ref), ref.name))
        return direct, string

    @staticmethod
    def _compute_pass_index(
        expressions: list[Expression],
    ) -> tuple[list[int | None], list[int | None]]:
        n = len(expressions)
        next_use: list[int | None] = [None] * n
        next_barrier: list[int | None] = [None] * n
        direct_last: dict[tuple, int] = {}
        string_last: dict[tuple, int] = {}
        last_barrier: int | None = None
        for i in range(n - 1, -1, -1):
            expr = expressions[i]
            next_barrier[i] = last_barrier
            if isinstance(expr, BinaryExpression) and isinstance(expr.left, Stat):
                dkey, skey = BinaryExpression._stat_query_keys(expr.left)
                d = direct_last.get(dkey)
                s = string_last.get(skey)
                if d is None:
                    next_use[i] = s
                elif s is None:
                    next_use[i] = d
                else:
                    next_use[i] = d if d < s else s
            dset, sset = BinaryExpression._expr_used_keys(expr)
            for k in dset:
                direct_last[k] = i
            for k in sset:
                string_last[k] = i
            if BinaryExpression._is_execution_barrier(expr):
                last_barrier = i
        return next_use, next_barrier

    @staticmethod
    def _remove_no_op_expressions(expressions: list[Expression]) -> bool:
        has_changed = False
        for i in range(len(expressions) - 1, -1, -1):
            _expression = expressions[i]

            if not isinstance(_expression, BinaryExpression):
                continue
            if is_preserved(_expression):
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
        has_changed = False
        use_index = _should_use_index(expressions)
        next_use: list[int | None] = []
        next_barrier: list[int | None] = []
        if use_index:
            next_use, next_barrier = BinaryExpression._compute_pass_index(expressions)
        i = 0
        while i < len(expressions) - 1:
            expr_i = expressions[i]
            if not (
                isinstance(expr_i, BinaryExpression)
                and isinstance(expr_i.left, Stat)
                and expr_i.operator is BinaryOperator.Set
                and not expr_i.is_intentional_self_assignment
                and not is_preserved(expr_i)
            ):
                i += 1
                continue

            lhs = expr_i.left
            init_value = expr_i.right

            # The first expression that touches lhs after i must be the identity
            # op, with no execution barrier reached before it.
            merge_target: BinaryExpression[Any, Any] | None = None
            if use_index:
                j = next_use[i]
                jb = next_barrier[i]
                if j is None or (jb is not None and jb < j):
                    i += 1
                    continue
                candidate = expressions[j]
                if (
                    isinstance(candidate, BinaryExpression)
                    and isinstance(candidate.left, Stat)
                    and candidate.left.is_same_stat(lhs)
                    and BinaryExpression._is_left_identity_for(
                        candidate.operator,
                        init_value,
                    )
                ):
                    merge_target = candidate
            else:
                j = i + 1
                while j < len(expressions):
                    expr_j = expressions[j]
                    if BinaryExpression._is_execution_barrier(expr_j):
                        break
                    if (
                        isinstance(expr_j, BinaryExpression)
                        and isinstance(expr_j.left, Stat)
                        and expr_j.left.is_same_stat(lhs)
                        and BinaryExpression._is_left_identity_for(
                            expr_j.operator,
                            init_value,
                        )
                    ):
                        merge_target = expr_j
                        break
                    if expr_j.is_using_stat(lhs):
                        break
                    j += 1

            if merge_target is None or is_preserved(merge_target):
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
            if use_index:
                # The list changed; recompute the forward index before continuing.
                next_use, next_barrier = BinaryExpression._compute_pass_index(
                    expressions,
                )
            i += 1

        return has_changed

    @staticmethod
    def _combine_constant_ops(
        op_a: BinaryOperator,
        val_a: int | float,
        op_b: BinaryOperator,
        val_b: int | float,
        internal_type: InternalType,
    ) -> tuple[BinaryOperator, int | float] | None:
        is_long = internal_type is InternalType.LONG
        both_int = isinstance(val_a, int) and isinstance(val_b, int)

        def fold_to(value: int | float) -> int | float | None:
            if isinstance(value, int) and not java_long.in_int64_range(value):
                return int(JavaLong(value)) if is_long else None
            return value

        if op_a is BinaryOperator.Set:
            if op_b is BinaryOperator.Increment:
                v = fold_to(val_a + val_b)
                return None if v is None else (BinaryOperator.Set, v)
            if op_b is BinaryOperator.Decrement:
                v = fold_to(val_a - val_b)
                return None if v is None else (BinaryOperator.Set, v)
            if op_b is BinaryOperator.Multiply:
                v = fold_to(val_a * val_b)
                return None if v is None else (BinaryOperator.Set, v)
            if both_int:
                assert isinstance(val_a, int) and isinstance(val_b, int)
                if op_b is BinaryOperator.BitwiseAnd:
                    v = fold_to(val_a & val_b)
                    return None if v is None else (BinaryOperator.Set, v)
                if op_b is BinaryOperator.BitwiseOr:
                    v = fold_to(val_a | val_b)
                    return None if v is None else (BinaryOperator.Set, v)
                if op_b is BinaryOperator.BitwiseXor:
                    v = fold_to(val_a ^ val_b)
                    return None if v is None else (BinaryOperator.Set, v)
                if op_b is BinaryOperator.LeftShift:
                    return BinaryOperator.Set, int(java_long.shl(val_a, val_b))
                if op_b is BinaryOperator.RightShift:
                    return BinaryOperator.Set, int(java_long.shr(val_a, val_b))
                if op_b is BinaryOperator.LogicalRightShift:
                    return BinaryOperator.Set, int(java_long.ushr(val_a, val_b))
            return None

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
                if both_int and not java_long.in_int64_range(val_a * val_b):
                    return None
                return op_a, val_a * val_b
            if both_int:
                assert isinstance(val_a, int) and isinstance(val_b, int)
                if op_a is BinaryOperator.BitwiseAnd:
                    v = fold_to(val_a & val_b)
                    return None if v is None else (op_a, v)
                if op_a is BinaryOperator.BitwiseOr:
                    v = fold_to(val_a | val_b)
                    return None if v is None else (op_a, v)
                if op_a is BinaryOperator.BitwiseXor:
                    v = fold_to(val_a ^ val_b)
                    return None if v is None else (op_a, v)
                if op_a in (
                    BinaryOperator.LeftShift,
                    BinaryOperator.RightShift,
                    BinaryOperator.LogicalRightShift,
                ):
                    if 0 <= val_a <= 63 and 0 <= val_b <= 63 and val_a + val_b <= 63:
                        return op_a, val_a + val_b
                    return None

        return None

    @staticmethod
    def _fold_consecutive_constant_ops(expressions: list[Expression]) -> bool:
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
                and not is_preserved(expr_a)
                and not is_preserved(expr_b)
            ):
                i += 1
                continue

            combined = BinaryExpression._combine_constant_ops(
                expr_a.operator,
                expr_a.right,
                expr_b.operator,
                expr_b.right,
                expr_a.left.internal_type,
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
    def _eliminate_dead_stores_scan(expressions: list[Expression]) -> bool:
        has_changed = False
        i = 0
        while i < len(expressions):
            expr_i = expressions[i]
            if not (
                isinstance(expr_i, BinaryExpression)
                and isinstance(expr_i.left, Stat)
                and not expr_i.is_intentional_self_assignment
                and not is_preserved(expr_i)
            ):
                i += 1
                continue

            lhs = expr_i.left
            is_dead = False
            for j in range(i + 1, len(expressions)):
                expr_j = expressions[j]
                if BinaryExpression._is_execution_barrier(expr_j):
                    break
                if not expr_j.is_using_stat(lhs):
                    continue
                if (
                    isinstance(expr_j, BinaryExpression)
                    and isinstance(expr_j.left, Stat)
                    and expr_j.left.is_same_stat(lhs)
                    and expr_j.operator is BinaryOperator.Set
                    and not expr_j.is_intentional_self_assignment
                    and not _rhs_references_stat(expr_j.right, lhs)
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
    def _eliminate_dead_stores(expressions: list[Expression]) -> bool:
        if not _should_use_index(expressions):
            return BinaryExpression._eliminate_dead_stores_scan(expressions)

        next_use, next_barrier = BinaryExpression._compute_pass_index(expressions)
        dead: list[int] = []
        for i in range(len(expressions)):
            expr_i = expressions[i]
            if not (
                isinstance(expr_i, BinaryExpression)
                and isinstance(expr_i.left, Stat)
                and not expr_i.is_intentional_self_assignment
                and not is_preserved(expr_i)
            ):
                continue

            lhs = expr_i.left
            j = next_use[i]
            jb = next_barrier[i]
            # A barrier (or the end of the block) reached before anything reads
            # or overwrites lhs leaves this store live.
            if j is None or (jb is not None and jb <= j):
                continue

            expr_j = expressions[j]
            if (
                isinstance(expr_j, BinaryExpression)
                and isinstance(expr_j.left, Stat)
                and expr_j.left.is_same_stat(lhs)
                and expr_j.operator is BinaryOperator.Set
                and not expr_j.is_intentional_self_assignment
                and not _rhs_references_stat(expr_j.right, lhs)
            ):
                dead.append(i)

        if not dead:
            return False
        # Deleting a dead store never changes another store's first-touch, so the
        # whole batch computed from one index is safe to drop at once.
        for i in reversed(dead):
            del expressions[i]
        return True

    @staticmethod
    def rename_temporary_stats(
        expressions: list[Expression],
        *,
        finalize: bool = False,
    ) -> None:
        reserved: set[int] = set(currently_reserved_temp_numbers())
        first_uses: list[TemporaryStat] = []
        seen: set[Number] = set()
        for expression in expressions:
            for expr in expression.walk_expressions():
                for stat, _ in expr.get_all_stats_used():
                    if isinstance(stat, TemporaryStat):
                        if stat._number.finalized:
                            reserved.add(stat.number)
                        elif stat._number not in seen:
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

        if finalize:
            for stat in first_uses:
                stat._number.finalized = True

    @staticmethod
    def optimize_binary_expressions(expressions: list[Expression]) -> None:
        # The temp-stat merge needs at least two expressions; for the very many
        # empty/one-line conditional bodies finalize produces, only the no-op
        # removal can apply.
        if len(expressions) < 2 or not optimization_enabled('temp_merge'):
            BinaryExpression.take_out_useless_expressions(expressions)
            return

        has_changed = True
        while has_changed:
            has_changed = False

            for i, _expression in enumerate(expressions):
                if not isinstance(_expression, BinaryExpression):
                    continue
                if is_preserved(_expression):
                    continue
                expression = _expression.into_assignment_expression()

                if not isinstance(expression.left, Stat):
                    continue
                if not isinstance(expression.right, TemporaryStat):
                    continue
                if expression.right._number.persistent:
                    continue
                if expression.operator is not BinaryOperator.Set:
                    continue
                if expression.left.is_same_stat(expression.right):
                    continue

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

                first_use = next(
                    (
                        j
                        for j in range(i)
                        if expressions[j].is_using_stat(expression.right)
                    ),
                    None,
                )
                if first_use is not None and any(
                    BinaryExpression._is_execution_barrier(expressions[j])
                    for j in range(first_use + 1, i)
                ):
                    continue

                # A list, not a generator: `any` must not short-circuit and
                # leave later occurrences un-rewritten.
                substitutions = [
                    expressions[j].change_all_occurrences_of_stat(
                        expression.right,
                        expression.left,
                    )
                    for j in range(i + 1)
                ]
                has_changed |= any(substitutions)

            # Inside the loop: a peephole fold can expose a new temp-stat merge.
            has_changed |= BinaryExpression.take_out_useless_expressions(expressions)

    def into_executable_expressions(self) -> Generator[Expression]:
        expressions = self.flatten()
        self.optimize_binary_expressions(expressions)
        self.rename_temporary_stats(expressions)
        yield from expressions

    def create_temp_stat_and_write(self) -> TemporaryStat:
        stat = TemporaryStat.transient()._as_type(self.internal_type)

        expressions = BinaryExpression(
            left=stat,
            right=self,
            operator=BinaryOperator.Set,
        ).flatten()
        self.optimize_binary_expressions(expressions)
        # Finalized: each lands in the block as its own statement and gets
        # re-rendered independently, so the numbers must not drift.
        self.rename_temporary_stats(expressions, finalize=True)
        for expr in expressions:
            expr.write()

        return stat

    def materialize(self) -> tuple[list[Expression], TemporaryStat]:
        stat = TemporaryStat.transient()._as_type(self.internal_type)
        expressions = BinaryExpression(
            left=stat,
            right=self.cloned(),
            operator=BinaryOperator.Set,
        ).flatten()
        return expressions, stat

    def into_string_lhs(self) -> str:
        return self.create_temp_stat_and_write().into_string_lhs()

    def into_string_rhs(self, *, include_internal_type: bool = True) -> str:
        return self.create_temp_stat_and_write().into_string_rhs(
            include_internal_type=include_internal_type,
        )

    def into_inside_string(self, include_fallback_value: bool = True) -> str:
        from pyhtsw.compiler.deferred import register_deferred

        return register_deferred(self, include_fallback_value)

    def into_htsl(self) -> str:
        field = 'The right-hand side of this assignment'

        def format_rhs(value: Checkable | HousingType) -> str:
            if isinstance(value, Checkable):
                return check_value_length(value.into_string_rhs(), field=field)
            if (
                isinstance(value, str)
                and no_type_casting()
                and _is_single_placeholder(value)
            ):
                return check_value_length(value, field=field)
            return check_value_length(housing_type_as_rhs(value), field=field)

        def into_line(expr: Expression) -> str:
            if not isinstance(expr, BinaryExpression):
                return expr.into_htsl()

            line = f'{expr.left.into_string_lhs()} {expr.operator.value} {format_rhs(expr.right)}'

            if isinstance(expr.left, Stat):
                line += f' {str(expr.left.auto_unset).lower()}'

            return line

        return '\n'.join(map(into_line, self.into_executable_expressions()))

    def cloned(
        self,
        *,
        left: LeftT | Missing = MISSING,
        right: RightT | Missing = MISSING,
        operator: BinaryOperator | Missing = MISSING,
        is_intentional_self_assignment: bool | Missing = MISSING,
        internal_type: InternalType | Missing = MISSING,
        fallback_value: HousingType | None | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'left': left,
                'right': right,
                'operator': operator,
                'is_intentional_self_assignment': is_intentional_self_assignment,
                'internal_type': internal_type,
                'fallback_value': fallback_value,
            },
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
        context: 'EmulatedHouse',
    ) -> None:
        right_value = BinaryExpression._resolve_assignment_rhs(
            expression.right,
            context,
        )

        if expression.operator is BinaryOperator.Set:
            BinaryExpression._store_assignment_result(
                expression.left,
                right_value,
                context,
            )
            return

        # htsw reads the left side by key, defaulting an unset variable to the
        # right side's type-zero (`holder.get(key, rhs.unsetValue())`).
        left_raw = context._get_raw(expression.left)
        left_value = (
            left_raw
            if left_raw is not None
            else backend_to_default_backend(right_value)
        )
        if isinstance(left_value, str) and not left_value:
            left_value = backend_to_default_backend(right_value)

        # In-game (verified 2026-08-18) a non-Set operation on mismatched
        # types is a FATAL error that halts execution — "You cannot add whole
        # numbers with decimal numbers" for long vs double, "The value
        # provided is not a number" for a string operand. Raising here models
        # the halt. (htsw's runtime under-modeled this as a warn + no-op.)
        if type(left_value) is not type(right_value):
            MismatchedTypeException.throw(
                left=(expression.left, left_value),
                right=(expression.right, right_value),
                operator=expression.operator,
            )
        if isinstance(left_value, str):
            NotANumberException.throw(
                left=(expression.left, left_value),
                right=(expression.right, right_value),
                operator=expression.operator,
            )

        if not isinstance(left_value, JavaLong | np.floating) or not isinstance(
            right_value,
            JavaLong | np.floating,
        ):
            raise RuntimeError(
                'Expected numeric values for binary expression execution',
            )

        if expression.operator in (
            BinaryOperator.BitwiseAnd,
            BinaryOperator.BitwiseOr,
            BinaryOperator.BitwiseXor,
            BinaryOperator.LeftShift,
            BinaryOperator.RightShift,
            BinaryOperator.LogicalRightShift,
        ):
            # Bitwise/shift operators are defined on longs only; a double
            # operand (which Java rejects at compile time) is first narrowed
            # with Java's `(long)` cast.
            original_is_double = isinstance(left_value, np.floating)
            if isinstance(left_value, np.floating) or isinstance(
                right_value,
                np.floating,
            ):
                left_long = java_long.from_double(float(left_value))
                right_long = java_long.from_double(float(right_value))
            else:
                left_long = left_value
                right_long = right_value

            if expression.operator is BinaryOperator.BitwiseAnd:
                result_long = java_long.bit_and(left_long, right_long)
            elif expression.operator is BinaryOperator.BitwiseOr:
                result_long = java_long.bit_or(left_long, right_long)
            elif expression.operator is BinaryOperator.BitwiseXor:
                result_long = java_long.bit_xor(left_long, right_long)
            elif expression.operator is BinaryOperator.LeftShift:
                result_long = java_long.shl(left_long, right_long)
            elif expression.operator is BinaryOperator.RightShift:
                result_long = java_long.shr(left_long, right_long)
            else:  # LogicalRightShift
                result_long = java_long.ushr(left_long, right_long)

            result = np.float64(int(result_long)) if original_is_double else result_long
            BinaryExpression._store_assignment_result(expression.left, result, context)
            return

        # Divide-by-zero keeps the old value as the result — a no-op in htsw,
        # which still runs the store-and-unset-flag step.
        if expression.operator is BinaryOperator.Divide and right_value == 0:
            BinaryExpression._store_assignment_result(
                expression.left,
                left_value,
                context,
            )
            return

        # Arithmetic operators. Longs and doubles never mix here (the type
        # check above already rejected that).
        if isinstance(left_value, np.floating):
            assert isinstance(right_value, np.floating)
            # `np.float64` is IEEE 754 binary64, exactly like a Java double;
            # numpy's warnings are silenced so overflow yields inf/nan as Java.
            with np.errstate(all='ignore'):
                if expression.operator is BinaryOperator.Increment:
                    result = np.float64(left_value + right_value)
                elif expression.operator is BinaryOperator.Decrement:
                    result = np.float64(left_value - right_value)
                elif expression.operator is BinaryOperator.Multiply:
                    result = np.float64(left_value * right_value)
                elif expression.operator is BinaryOperator.Divide:
                    result = np.float64(left_value / right_value)
                else:
                    raise ValueError(f'Unexpected operator: {expression.operator}')
        else:
            assert isinstance(right_value, JavaLong)
            if expression.operator is BinaryOperator.Increment:
                result = java_long.add(left_value, right_value)
            elif expression.operator is BinaryOperator.Decrement:
                result = java_long.sub(left_value, right_value)
            elif expression.operator is BinaryOperator.Multiply:
                result = java_long.mul(left_value, right_value)
            elif expression.operator is BinaryOperator.Divide:
                result = java_long.div(left_value, right_value)
            else:
                raise ValueError(f'Unexpected operator: {expression.operator}')

        BinaryExpression._store_assignment_result(expression.left, result, context)

    @staticmethod
    def _resolve_assignment_rhs(
        rhs: 'Checkable | HousingType',
        context: 'EmulatedHouse',
    ) -> BackendType:
        from pyhtsw.execute.value_parser import parse_string, parse_value

        if isinstance(rhs, Checkable):
            return parse_value(context, rhs.into_string_rhs())
        if isinstance(rhs, str):
            if no_type_casting() and _is_single_placeholder(rhs):
                # Emitted as a raw bare value.
                return parse_value(context, rhs)
            # Everything else is emitted as a quoted string: one pass.
            return parse_string(context, rhs)
        return into_backend_type(rhs)

    @staticmethod
    def _store_assignment_result(
        left: Editable,
        result: BackendType,
        context: 'EmulatedHouse',
    ) -> None:
        if isinstance(left, Stat) and left.auto_unset and is_default_backend(result):
            context.pop(left)
            return
        context.put(left, result, ignore_warning=True)

    def raw_execute(self, context: 'EmulatedHouse') -> None:
        for expr in self.into_executable_expressions():
            if not isinstance(expr, BinaryExpression):
                expr.execute(context)
                continue
            expr = expr.into_assignment_expression()
            if context.verbose:
                log(
                    f'{" " * 4}Executing \x1b[38;2;255;0;0m"{expr.left!r} {expr.operator.value} {expr.right!r}"\x1b[0m',
                )
                log(
                    f'{" " * 8}BEFORE: {expr.left.into_string_lhs()} = {descriptive_backend_type(context._get_raw(expr.left))}',
                )
            self.execute_assignment_expression(expr, context)
            if context.verbose:
                log(
                    f'{" " * 8}AFTER:  {expr.left.into_string_lhs()} = {descriptive_backend_type(context._get_raw(expr.left))}',
                )
