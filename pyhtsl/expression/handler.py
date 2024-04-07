from .expr_type import ExpressionType

from typing import TYPE_CHECKING, final, ClassVar
if TYPE_CHECKING:
    from .expr_class import Expression
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
            stat.name = f'temp{i}'
            stat.number = i

    def create_lines(self) -> list[tuple['Stat', 'ExpressionType', 'Stat | int']]:
        lines: list[tuple['Stat', 'ExpressionType', 'Stat | int']] = []
        for expression in self.__expressions:
            left = expression.fetch_stat_or_int(expression.left)
            right = expression.fetch_stat_or_int(expression.right)
            lines.append((left, expression.type, right))
        return lines

    def optimize_lines(self, lines: list[tuple['Stat', 'ExpressionType', 'Stat | int']]) -> None:
        pass

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

    def push(self) -> None:
        self.rename_temporary_stats()
        lines = self.create_lines()
        self.optimize_lines(lines)
        self.take_out_useless(lines)
        print('\n'.join(f'{repr(left)} {type.value} {repr(right)}' for left, type, right in lines))
        self.__expressions.clear()


EXPR_HANDLER = ExpressionHandler()
