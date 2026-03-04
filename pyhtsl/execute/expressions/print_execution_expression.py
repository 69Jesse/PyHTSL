from typing import TYPE_CHECKING, Self

from .execution_expression import ExecutionExpression

if TYPE_CHECKING:
    from ..context import ExecutionContext


__all__ = ('PrintExecutionExpression',)


class PrintExecutionExpression(ExecutionExpression):
    line: str

    def __init__(self, line: str) -> None:
        self.line = line

    def cloned(self) -> Self:
        return self.__class__(line=self.line)

    def equals(self, other: object) -> bool:
        if not isinstance(other, PrintExecutionExpression):
            return False
        return self.line == other.line

    def __repr__(self) -> str:
        return f'PrintExecutionExpression(line={self.line!r})'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        print(context.replace_placeholders(self.line))
