from .expression_type import ExpressionType
from ..writer import WRITER

from typing import TYPE_CHECKING, final, ClassVar
if TYPE_CHECKING:
    from .expression import Expression
    from ..stat import Stat, TemporaryStat
    from ..condition import PlaceholderValue


__all__ = (
    'EXPR_HANDLER',
)


TEMP_STATS_NUMBER_START: int = 1
LinesType = list[tuple['Stat', ExpressionType, 'Stat | int | PlaceholderValue']]


@final
class ExpressionHandler:
    _expressions: list['Expression'] = []
    temporary_stat_cls: ClassVar[type['TemporaryStat']]

    def add(self, expression: 'Expression') -> None:
        self._expressions.append(expression)

    def is_empty(self) -> bool:
        return not self._expressions

    def create_lines(self) -> LinesType:
        lines: LinesType = []
        for expression in self._expressions:
            left = expression.fetch_stat_or_int(expression.left)
            if TYPE_CHECKING:
                assert isinstance(left, Stat)
            right = expression.fetch_stat_or_int(expression.right)
            lines.append((left, expression.type, right))
        return lines

    def optimize_lines(
        self,
        lines: LinesType,
    ) -> None:
        has_changed = True
        while has_changed:
            has_changed = False
            for i in range(len(lines)):
                left, expr_type, right = lines[i]

                if not isinstance(left, self.temporary_stat_cls):
                    if not isinstance(right, self.temporary_stat_cls):
                        continue
                    if expr_type is not ExpressionType.Set:
                        continue

                    # We have:
                    # `stat = tempstat`
                    # this means that
                    #     - we can replace all previous tempstat with stat
                    #     - but ONLY IF
                    #         * stat is not used before this line in relation with tempstat
                    #         * tempstat is not used after this line

                    used_before = False
                    for j in range(i - 1, -1, -1):
                        other_left, other_type, other_right = lines[j]
                        if (
                            type(other_left) is type(left) and other_left.name == left.name
                            and isinstance(other_right, self.temporary_stat_cls) and other_right.number == right.number
                        ):
                            used_before = True
                            break
                        if (
                            isinstance(other_left, self.temporary_stat_cls) and other_left.number == right.number
                            and type(other_right) is type(left) and other_right.name == left.name  # type: ignore
                        ):
                            used_before = True
                            break
                    if used_before:
                        continue

                    used_after = False
                    for j in range(i + 1, len(lines)):
                        other_left, other_type, other_right = lines[j]
                        if isinstance(other_left, self.temporary_stat_cls) and other_left.number == right.number:
                            used_after = True
                            break
                        if isinstance(other_right, self.temporary_stat_cls) and other_right.number == right.number:
                            used_after = True
                            break
                    if used_after:
                        continue

                    for j in range(i, -1, -1):
                        other_left, other_type, other_right = lines[j]
                        changing = False
                        if isinstance(other_left, self.temporary_stat_cls) and other_left.number == right.number:
                            other_left = left
                            changing = True
                        if isinstance(other_right, self.temporary_stat_cls) and other_right.number == right.number:
                            other_right = left
                            changing = True
                        if changing:
                            lines[j] = (other_left, other_type, other_right)
                            has_changed = True

                    continue

                else:
                    if not isinstance(right, self.temporary_stat_cls):
                        continue
                    if expr_type is not ExpressionType.Set:
                        continue

                    # We have:
                    # `tempstat1 = tempstat2`
                    # this means that
                    #     - we can replace all previous tempstat2 with tempstat1
                    #     - but ONLY IF
                    #         * tempstat1 is not used before this line in relation with tempstat2
                    #         * tempstat2 is not used after this line

                    used_before = False
                    for j in range(i - 1, -1, -1):
                        other_left, other_type, other_right = lines[j]
                        if (
                            isinstance(other_left, self.temporary_stat_cls) and other_left.number == left.number
                            and isinstance(other_right, self.temporary_stat_cls) and other_right.number == right.number
                        ):
                            used_before = True
                            break
                        if (
                            isinstance(other_left, self.temporary_stat_cls) and other_left.number == right.number
                            and isinstance(other_right, self.temporary_stat_cls) and other_right.number == left.number
                        ):
                            used_before = True
                            break

                    used_after = False
                    for j in range(i + 1, len(lines)):
                        other_left, other_type, other_right = lines[j]
                        if isinstance(other_left, self.temporary_stat_cls) and other_left.number == right.number:
                            used_after = True
                            break
                        if isinstance(other_right, self.temporary_stat_cls) and other_right.number == right.number:
                            used_after = True
                            break
                    if used_after:
                        continue

                    for j in range(i, -1, -1):
                        other_left, other_type, other_right = lines[j]
                        changing = False
                        if isinstance(other_left, self.temporary_stat_cls) and other_left.number == right.number:
                            other_left = left
                            changing = True
                        if isinstance(other_right, self.temporary_stat_cls) and other_right.number == right.number:
                            other_right = left
                            changing = True
                        if changing:
                            lines[j] = (other_left, other_type, other_right)
                            has_changed = True

    def take_out_useless(
        self,
        lines: LinesType,
    ) -> None:
        for i in range(len(lines) - 1, -1, -1):
            left, expr_type, right = lines[i]
            if (
                expr_type is ExpressionType.Set
                and not isinstance(right, int)
                and left.name == right.name
                and type(left) is type(right)
            ):
                lines.pop(i)
            elif (
                (expr_type is ExpressionType.Increment or expr_type is ExpressionType.Decrement)
                and isinstance(right, int)
                and right == 0
            ):
                lines.pop(i)
            elif (
                (expr_type is ExpressionType.Multiply or expr_type is ExpressionType.Divide)
                and isinstance(right, int)
                and right == 1
            ):
                lines.pop(i)

    def rename_temporary_stats(
        self,
        lines: LinesType,
    ) -> None:
        temporary_stats: list['TemporaryStat'] = []
        stat_id_set: set[int] = set()
        for stat, _, _ in lines:
            if id(stat) in stat_id_set:
                continue
            if isinstance(stat, self.temporary_stat_cls):
                temporary_stats.append(stat)
            stat_id_set.add(id(stat))
        for i, stat in enumerate(temporary_stats, start=TEMP_STATS_NUMBER_START):
            stat.number = i

    def write_lines(
        self,
        lines: LinesType,
    ) -> None:
        for left, type, right in lines:
            WRITER.write(
                f'{left.operational_expression_left_side()} {type.value} "{str(right)}"',
                left.line_type,
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
