from typing import TYPE_CHECKING, final, ClassVar
if TYPE_CHECKING:
    from .classes import Expression
    from ..stat import TemporaryStat


__all__ = (
    'EXPR_HANDLER',
)


@final
class ExpressionHandler:
    __expressions: list['Expression'] = []
    temporary_stat_cls: ClassVar[type['TemporaryStat']]

    def add(self, expression: 'Expression') -> None:
        self.__expressions.append(expression)

    def push(self) -> None:
        print(f'pushing with {len(self.__expressions)} expressions')

        print('\n'.join(map(str, self.__expressions)))
        self.__expressions.clear()


EXPR_HANDLER = ExpressionHandler()
