from typing import Self, final

from ..expression.expression import Expression

__all__ = ('exit_function',)


@final
class ExitFunctionExpression(Expression):
    def into_htsl(self) -> str:
        return 'exit'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, ExitFunctionExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def exit_function() -> None:
    ExitFunctionExpression().write()
