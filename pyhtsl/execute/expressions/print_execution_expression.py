from typing import TYPE_CHECKING, Self

from ...utils.log import log
from .execution_expression import ExecutionExpression

if TYPE_CHECKING:
    from ..context import ExecutionContext


__all__ = ('PrintExecutionExpression',)


class PrintExecutionExpression(ExecutionExpression):
    line: str
    cast: bool

    def __init__(self, line: str, *, cast: bool = False) -> None:
        self.line = line
        self.cast = cast

    def cloned(self) -> Self:
        return self.__class__(line=self.line, cast=self.cast)

    def equals(self, other: object) -> bool:
        if not isinstance(other, PrintExecutionExpression):
            return False
        return self.line == other.line and self.cast == other.cast

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(line={self.line!r}, cast={self.cast!r})'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        log(context.get(self.line, cast=self.cast, output='string'))
