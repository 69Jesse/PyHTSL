from ..condition.binary_condition import BinaryCondition
from ..writer import WRITER
from ..public.no_optimization import no_optimization

from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from ..stats.base_stat import BaseStat
    from ..stats.temporary_stat import TemporaryStat
    from ..checkable import Checkable
    from ..editable import Editable
    from .housing_type import HousingType
    from .expression import Expression
    from .conditional_expressions import ConditionalEnterExpression, ConditionalExitExpression
    from .binary_expression import BinaryExpressionOperator, BinaryExpression


__all__ = (
    'AUTOMATIC_UNSET',
    'EXPR_HANDLER',
)


TEMP_STATS_NUMBER_START: int = 1


class AutomaticUnset:
    counter: int = 0

    def increment(self) -> None:
        self.counter += 1

    def decrement(self) -> None:
        self.counter -= 1

    @property
    def value(self) -> bool:
        return self.counter == 0


AUTOMATIC_UNSET: AutomaticUnset = AutomaticUnset()


@final
class ExpressionHandler:
    @staticmethod
    def _import_checkable(
        checkable_cls: type['Checkable'],
    ) -> None:
        globals()[checkable_cls.__name__] = checkable_cls

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
        globals()[conditional_enter_expression_cls.__name__] = conditional_enter_expression_cls
        globals()[conditional_exit_expression_cls.__name__] = conditional_exit_expression_cls

    _expressions: list['Expression'] = []

    def add(self, expression: 'Expression') -> None:
        self._expressions.append(expression)

    def is_empty(self) -> bool:
        return not self._expressions

    @staticmethod
    def used_before(
        expressions: list['Expression'],
        left: 'Editable',
        right: 'Editable',
        indexes: range,
    ) -> bool:
        for j in indexes:
            other_expression = expressions[j]
            if isinstance(other_expression, BinaryExpression):
                if left.equals(
                    other_expression.left,
                    check_internal_type=False,
                ) and right.equals(
                    other_expression.right,
                    check_internal_type=False,
                ):
                    return True
                if (
                    right.equals(
                        other_expression.left,
                        check_internal_type=False,
                    )
                    and left.equals(
                        other_expression.right,
                        check_internal_type=False,
                    )
                    and other_expression.operator is not BinaryExpressionOperator.Set
                ):
                    return True
            elif isinstance(other_expression, ConditionalEnterExpression):
                if any(
                    (
                        left.equals(
                            cond.left,
                            check_internal_type=False,
                        )
                        and right.equals(
                            cond.right,
                            check_internal_type=False,
                        )
                    )
                    or (
                        left.equals(
                            cond.right,
                            check_internal_type=False,
                        )
                        and right.equals(
                            cond.left,
                            check_internal_type=False,
                        )
                    )
                    for cond in other_expression.statement.conditions
                    if isinstance(cond, BinaryCondition)
                ):
                    return True
        return False

    @staticmethod
    def used_after(
        expressions: list['Expression'],
        right: 'Editable',
        indexes: range,
    ) -> bool:
        for j in indexes:
            other_expression = expressions[j]
            if isinstance(other_expression, BinaryExpression):
                if right.equals(
                    other_expression.left,
                    check_internal_type=False,
                ):
                    return True
                if right.equals(
                    other_expression.right,
                    check_internal_type=False,
                ):
                    return True
            elif isinstance(other_expression, ConditionalEnterExpression):
                if any(
                    (
                        right.equals(
                            cond.left,
                            check_internal_type=False,
                        )
                        or right.equals(
                            cond.right,
                            check_internal_type=False,
                        )
                    )
                    for cond in other_expression.statement.conditions
                    if isinstance(cond, BinaryCondition)
                ):
                    return True
        return False

    @staticmethod
    def change_all(
        expressions: list['Expression'],
        left: 'Editable',
        right: 'Editable',
        indexes: range,
    ) -> bool:
        has_changed: bool = False
        for j in indexes:
            other_expression = expressions[j]
            if isinstance(other_expression, BinaryExpression):
                if right.equals(
                    other_expression.left, check_internal_type=False
                ):
                    other_expression.left = left
                    has_changed = True
                if right.equals(
                    other_expression.right, check_internal_type=False
                ):
                    other_expression.right = left
                    has_changed = True
            elif isinstance(other_expression, ConditionalEnterExpression):
                for condition in other_expression.statement.conditions:
                    if not isinstance(condition, BinaryCondition):
                        continue
                    if right.equals(
                        condition.left, check_internal_type=False
                    ):
                        condition.left = left
                        has_changed = True
                    if right.equals(
                        condition.right, check_internal_type=False
                    ):
                        condition.right = left
                        has_changed = True
        return has_changed

    @staticmethod
    def optimize_lines(expressions: list['Expression']) -> None:
        for expression in expressions[:-1]:
            if not isinstance(expression, BinaryExpression):
                continue
            assert isinstance(expression.left, TemporaryStat)

        has_changed = True
        while has_changed:
            has_changed = False
            for i, expression in enumerate(expressions):
                if not isinstance(expression, BinaryExpression):
                    continue

                if not isinstance(expression.right, TemporaryStat):
                    continue
                if expression.operator is not BinaryExpressionOperator.Set:
                    continue

                # We have:
                # `left = right`
                # this means that
                #     - we can replace all previous right with left
                #     - but ONLY IF
                #         * left is not used before this line in relation with right
                #             the exception being `right = left`
                #         * right is not used after this line

                if ExpressionHandler.used_before(
                    expressions,
                    expression.left,
                    expression.right,
                    range(i - 1, -1, -1),
                ):
                    continue

                if ExpressionHandler.used_after(
                    expressions,
                    expression.right,
                    range(i + 1, len(expressions)),
                ):
                    continue

                has_changed |= ExpressionHandler.change_all(
                    expressions,
                    expression.left,
                    expression.right,
                    range(i + 1),
                )

    @staticmethod
    def take_out_useless(expressions: list['Expression']) -> None:
        for i in range(len(expressions) - 1, -1, -1):
            expression = expressions[i]
            if not isinstance(expression, BinaryExpression):
                continue

            if (
                expression.left.equals(expression.right, check_internal_type=False)
                and expression.operator is BinaryExpressionOperator.Set
                and not expression.is_self_cast
            ):
                expressions.pop(i)
            elif (
                expression.operator is BinaryExpressionOperator.Increment
                or expression.operator is BinaryExpressionOperator.Decrement
            ) and (
                (isinstance(expression.right, int) and expression.right == 0)
                or (isinstance(expression.right, float) and expression.right == 0.0)
            ):
                expressions.pop(i)
            elif (
                expression.operator is BinaryExpressionOperator.Multiply
                or expression.operator is BinaryExpressionOperator.Divide
            ) and (
                (isinstance(expression.right, int) and expression.right == 1)
                or (isinstance(expression.right, float) and expression.right == 1.0)
            ):
                expressions.pop(i)

    @staticmethod
    def _add_to_temporary_stats_mapping(
        value: 'Checkable | HousingType',
        temporary_stats: dict[int, list['TemporaryStat']],
    ) -> None:
        if isinstance(value, BinaryExpression):
            ExpressionHandler._add_to_temporary_stats_mapping(
                value._left, temporary_stats
            )
            ExpressionHandler._add_to_temporary_stats_mapping(
                value._right, temporary_stats
            )
        if not isinstance(value, TemporaryStat):
            return
        temporary_stats.setdefault(value.number, []).append(value)

    @staticmethod
    def rename_temporary_stats(expressions: list['Expression']) -> None:
        temporary_stats: dict[int, list['TemporaryStat']] = {}
        for expression in expressions:
            if not isinstance(expression, BinaryExpression):
                continue
            ExpressionHandler._add_to_temporary_stats_mapping(
                expression.left, temporary_stats
            )
            ExpressionHandler._add_to_temporary_stats_mapping(
                expression.right, temporary_stats
            )
        for i, stats in enumerate(
            temporary_stats.values(),
            start=TEMP_STATS_NUMBER_START,
        ):
            for stat in stats:
                stat.number = i

    @staticmethod
    def validate_lines(expressions: list['Expression']) -> None:
        for expression in expressions:
            if not isinstance(expression, BinaryExpression):
                continue
            if isinstance(expression.right, str) and len(expression.right) > 32:
                raise ValueError(
                    f'Assignment of string "{expression.right}" is too long ({len(expression.right)}>32)'
                )

    @staticmethod
    def write_lines(expressions: list['Expression']) -> None:
        for expression in expressions:
            expression._before_write_line()
            WRITER.write(*expression._write_line())
            expression._after_write_line()

    def push(self) -> None:
        if self.is_empty():
            return
        expressions = self._expressions.copy()
        self._expressions.clear()
        if not no_optimization():
            ExpressionHandler.optimize_lines(expressions)
            ExpressionHandler.take_out_useless(expressions)
        ExpressionHandler.rename_temporary_stats(expressions)
        ExpressionHandler.validate_lines(expressions)
        ExpressionHandler.write_lines(expressions)
        container = WRITER.get_container()
        if container.expressions_callback is not None:
            container.expressions_callback(expressions)


EXPR_HANDLER = ExpressionHandler()
