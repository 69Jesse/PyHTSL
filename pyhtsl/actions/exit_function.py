from typing import TYPE_CHECKING, Self, final

from ..expression.expression import Expression

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext


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

    def raw_execute(self, context: 'ExecutionContext') -> None:
        from ..execute.exception import ExitExpressionException

        raise ExitExpressionException()


def exit_function() -> None:
    ExitFunctionExpression().write()
