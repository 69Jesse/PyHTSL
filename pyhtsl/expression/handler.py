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
    __expressions: list['Expression'] = []
    temporary_stat_cls: ClassVar[type['TemporaryStat']]

    def add(self, expression: 'Expression') -> None:
        self.__expressions.append(expression)

    def is_empty(self) -> bool:
        return not self.__expressions

    def create_lines(self) -> LinesType:
        lines: LinesType = []
        for expression in self.__expressions:
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
        skipping_temporary_stats: set['TemporaryStat'] = set()
        for i in range(len(lines)):
            left, type, right = lines[i]

            if not isinstance(left, self.temporary_stat_cls):
                if not isinstance(right, self.temporary_stat_cls):
                    continue
                if type is not ExpressionType.Set:
                    continue
                # stat = tempstat -> all previous tempstat to stat
                for j in range(i, -1, -1):
                    new_left, new_type, new_right = lines[j]
                    if isinstance(new_left, self.temporary_stat_cls) and new_left.number == right.number:
                        new_left = left
                    if isinstance(new_right, self.temporary_stat_cls) and new_right.number == right.number:
                        new_right = left
                    lines[j] = (new_left, new_type, new_right)
                continue

            if isinstance(right, self.temporary_stat_cls) and type is ExpressionType.Set:
                # l-tempstat = r-tempstat -> all next l-tempstat to r-tempstat
                lines[i] = (right, type, right)
                for j in range(i + 1, len(lines)):
                    new_left, new_type, new_right = lines[j]
                    if isinstance(new_left, self.temporary_stat_cls) and new_left.number == left.number:
                        new_left = right
                    if isinstance(new_right, self.temporary_stat_cls) and new_right.number == left.number:
                        new_right = right
                    lines[j] = (new_left, new_type, new_right)
                continue

            # check for possible lower number to avoid using unnecessary temporary stats
            if left in skipping_temporary_stats:
                continue
            for number in range(TEMP_STATS_NUMBER_START, left.number):
                for j in range(i, len(lines)):
                    new_left, new_type, new_right = lines[j]
                    if (
                        isinstance(new_left, self.temporary_stat_cls)
                        and new_left.number == number
                        and new_type is not ExpressionType.Set
                    ):
                        break
                    if (
                        isinstance(new_right, self.temporary_stat_cls)
                        and new_right.number == number
                    ):
                        break
                else:
                    left.number = number
                    break
            else:
                skipping_temporary_stats.add(left)

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
        self.__expressions.clear()


EXPR_HANDLER = ExpressionHandler()
