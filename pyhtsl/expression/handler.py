from ..writer import WRITER, LineType

from typing import TYPE_CHECKING, final, TypeAlias
if TYPE_CHECKING:
    from ..stats.temporary_stat import TemporaryStat
    from ..checkable import Checkable
    from .housing_type import HousingType
    from ..editable import Editable
    from .assignment_expression import Expression, ExpressionOperator


__all__ = (
    'EXPR_HANDLER',
)


TEMP_STATS_NUMBER_START: int = 1
Lines: TypeAlias = list[tuple['Editable', 'ExpressionOperator', 'Checkable | HousingType']]


@final
class ExpressionHandler:
    @staticmethod
    def _import_checkable(
        checkable_cls: type['Checkable'],
    ) -> None:
        globals()[checkable_cls.__name__] = checkable_cls

    @staticmethod
    def _import_temporary_stat(
        temporary_stat_cls: type['TemporaryStat'],
    ) -> None:
        globals()[temporary_stat_cls.__name__] = temporary_stat_cls

    @staticmethod
    def _import_expression_operator(
        expression_operator_cls: type['ExpressionOperator'],
    ) -> None:
        globals()[expression_operator_cls.__name__] = expression_operator_cls

    _expressions: list['Expression'] = []

    def add(self, expression: 'Expression') -> None:
        self._expressions.append(expression)

    def is_empty(self) -> bool:
        return not self._expressions

    def create_lines(self) -> Lines:
        lines: Lines = []
        for expression in self._expressions:
            left = expression._all_the_way_left(expression.left)
            right = expression._all_the_way_left(expression.right)
            lines.append((left, expression.operator, right))
        return lines

    def optimize_lines(
        self,
        lines: Lines,
    ) -> None:
        for i in range(len(lines) - 1):
            left, _, _ = lines[i]
            assert isinstance(left, TemporaryStat)

        has_changed = True
        while has_changed:
            has_changed = False
            for i in range(len(lines)):
                left, operator, right = lines[i]

                if not isinstance(left, TemporaryStat):
                    if not isinstance(right, TemporaryStat):
                        continue
                    if operator is not ExpressionOperator.Set:
                        continue

                    # We have:
                    # `stat = tempstat`
                    # this means that
                    #     - we can replace all previous tempstat with stat
                    #     - but ONLY IF
                    #         * stat is not used before this line in relation with tempstat
                    #             the exception being `tempstat = stat`
                    #         * tempstat is not used after this line

                    used_before = False
                    for j in range(i - 1, -1, -1):
                        other_left, other_operator, other_right = lines[j]
                        assert type(other_left) is not type(left)
                        if (
                            isinstance(other_left, TemporaryStat) and other_left.number == right.number
                            and type(other_right) is type(left) and other_right.name == left.name  # type: ignore
                            and other_operator is not ExpressionOperator.Set
                        ):
                            used_before = True
                            break
                    if used_before:
                        continue

                    used_after = False
                    for j in range(i + 1, len(lines)):
                        other_left, other_operator, other_right = lines[j]
                        if isinstance(other_left, TemporaryStat) and other_left.number == right.number:
                            used_after = True
                            break
                        if isinstance(other_right, TemporaryStat) and other_right.number == right.number:
                            used_after = True
                            break
                    if used_after:
                        continue

                    for j in range(i, -1, -1):
                        other_left, other_operator, other_right = lines[j]
                        changing = False
                        if isinstance(other_left, TemporaryStat) and other_left.number == right.number:
                            other_left = left
                            changing = True
                        if isinstance(other_right, TemporaryStat) and other_right.number == right.number:
                            other_right = left
                            changing = True
                        if changing:
                            lines[j] = (other_left, other_operator, other_right)
                            has_changed = True

                    continue

                else:
                    if not isinstance(right, TemporaryStat):
                        continue
                    if operator is not ExpressionOperator.Set:
                        continue

                    # We have:
                    # `tempstat1 = tempstat2`
                    # this means that
                    #     - we can replace all previous tempstat2 with tempstat1
                    #     - but ONLY IF
                    #         * tempstat1 is not used before this line in relation with tempstat2
                    #             the exception being `tempstat2 = tempstat1`
                    #         * tempstat2 is not used after this line

                    used_before = False
                    for j in range(i - 1, -1, -1):
                        other_left, other_operator, other_right = lines[j]
                        if (
                            isinstance(other_left, TemporaryStat) and other_left.number == left.number
                            and isinstance(other_right, TemporaryStat) and other_right.number == right.number
                        ):
                            used_before = True
                            break
                        if (
                            isinstance(other_left, TemporaryStat) and other_left.number == right.number
                            and isinstance(other_right, TemporaryStat) and other_right.number == left.number
                            and other_operator is not ExpressionOperator.Set
                        ):
                            used_before = True
                            break

                    used_after = False
                    for j in range(i + 1, len(lines)):
                        other_left, other_operator, other_right = lines[j]
                        if isinstance(other_left, TemporaryStat) and other_left.number == right.number:
                            used_after = True
                            break
                        if isinstance(other_right, TemporaryStat) and other_right.number == right.number:
                            used_after = True
                            break
                    if used_after:
                        continue

                    for j in range(i, -1, -1):
                        other_left, other_operator, other_right = lines[j]
                        changing = False
                        if isinstance(other_left, TemporaryStat) and other_left.number == right.number:
                            other_left = left
                            changing = True
                        if isinstance(other_right, TemporaryStat) and other_right.number == right.number:
                            other_right = left
                            changing = True
                        if changing:
                            lines[j] = (other_left, other_operator, other_right)
                            has_changed = True

    def take_out_useless(
        self,
        lines: Lines,
    ) -> None:
        for i in range(len(lines) - 1, -1, -1):
            left, operator, right = lines[i]
            if (
                left._equals(right)
                and operator is ExpressionOperator.Set
            ):
                lines.pop(i)
            elif (
                (operator is ExpressionOperator.Increment or operator is ExpressionOperator.Decrement)
                and ((isinstance(right, int) and right == 0) or (isinstance(right, float) and right == 0.0))
            ):
                lines.pop(i)
            elif (
                (operator is ExpressionOperator.Multiply or operator is ExpressionOperator.Divide)
                and ((isinstance(right, int) and right == 1) or (isinstance(right, float) and right == 1.0))
            ):
                lines.pop(i)

    def rename_temporary_stats(
        self,
        lines: Lines,
    ) -> None:
        temporary_stats: list['TemporaryStat'] = []
        stat_id_set: set[int] = set()
        for stat, _, _ in lines:
            if id(stat) in stat_id_set:
                continue
            if isinstance(stat, TemporaryStat):
                temporary_stats.append(stat)
            stat_id_set.add(id(stat))
        for i, stat in enumerate(temporary_stats, start=TEMP_STATS_NUMBER_START):
            stat.number = i

    def write_lines(
        self,
        lines: Lines,
    ) -> None:
        for left, operator, right in lines:
            WRITER.write(
                f'{left._in_assignment_left_side()} {operator.value} {Checkable._to_assignment_right_side(right)}',
                LineType.variable_change,
            )

    def push(self) -> None:
        if self.is_empty():
            return
        lines = self.create_lines()
        self.optimize_lines(lines)
        self.take_out_useless(lines)
        self.rename_temporary_stats(lines)
        self.write_lines(lines)
        self._expressions.clear()


EXPR_HANDLER = ExpressionHandler()
