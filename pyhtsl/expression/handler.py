from .expression_type import ExpressionType
from ..write import write

from typing import TYPE_CHECKING, final, ClassVar
if TYPE_CHECKING:
    from .expression import Expression
    from ..stat import Stat, TemporaryStat


__all__ = (
    'EXPR_HANDLER',
)


TEMP_STATS_NUMBER_START: int = 1


@final
class ExpressionHandler:
    __expressions: list['Expression'] = []
    temporary_stat_cls: ClassVar[type['TemporaryStat']]

    def add(self, expression: 'Expression') -> None:
        self.__expressions.append(expression)

    def rename_temporary_stats(self) -> None:
        temporary_stats: list['TemporaryStat'] = []
        for expression in self.__expressions:
            stat = expression.fetch_stat_or_int(expression.left)
            if isinstance(stat, self.temporary_stat_cls) and stat not in temporary_stats:
                temporary_stats.append(stat)
        for i, stat in enumerate(temporary_stats, start=TEMP_STATS_NUMBER_START):
            stat.number = i

    def create_lines(self) -> list[tuple['Stat', 'ExpressionType', 'Stat | int']]:
        lines: list[tuple['Stat', 'ExpressionType', 'Stat | int']] = []
        for expression in self.__expressions:
            left = expression.fetch_stat_or_int(expression.left)
            right = expression.fetch_stat_or_int(expression.right)
            lines.append((left, expression.type, right))
        return lines

    def optimize_lines(self, lines: list[tuple['Stat', 'ExpressionType', 'Stat | int']]) -> None:
        for i in range(len(lines)):
            left, type, right = lines[i]
            if not isinstance(left, self.temporary_stat_cls):
                continue
            for number in range(TEMP_STATS_NUMBER_START, left.number):
                for j in range(i + 1, len(lines)):
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

    def take_out_useless(self, lines: list[tuple['Stat', 'ExpressionType', 'Stat | int']]) -> None:
        for i in range(len(lines) - 1, -1, -1):
            left, type, right = lines[i]
            if (
                type is ExpressionType.Set
                and not isinstance(right, int)
                and right.name == left.name
            ):
                lines.pop(i)
            elif (
                (type is ExpressionType.Increment or type is ExpressionType.Decrement)
                and isinstance(right, int)
                and right == 0
            ):
                lines.pop(i)
            elif (
                (type is ExpressionType.Multiply or type is ExpressionType.Divide)
                and isinstance(right, int)
                and right == 1
            ):
                lines.pop(i)

    def write_lines(self, lines: list[tuple['Stat', 'ExpressionType', 'Stat | int']]) -> None:
        for left, type, right in lines:
            write(f'{repr(left)} {type.value} {str(right)}')

    def push(self) -> None:
        self.rename_temporary_stats()
        lines = self.create_lines()
        self.optimize_lines(lines)
        self.take_out_useless(lines)
        self.write_lines(lines)
        self.__expressions.clear()


EXPR_HANDLER = ExpressionHandler()
