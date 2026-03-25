from typing import TYPE_CHECKING, Self, final

from pyhtsl.utils.formatting import formatting_to_ansi
from pyhtsl.utils.log import log

from ..expression.expression import Expression

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext


__all__ = ('chat',)


@final
class ChatExpression(Expression):
    line: str

    def __init__(self, line: str) -> None:
        self.line = line

    def into_htsl(self) -> str:
        return f'chat {self.inline_quoted(self.line)}'

    def cloned(self) -> Self:
        return self.__class__(line=self.line)

    def equals(self, other: object) -> bool:
        if not isinstance(other, ChatExpression):
            return False
        return self.line == other.line

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.line}>'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        log(formatting_to_ansi(f'&7* &f{context.substitute(self.line, cast=False)}'))


def chat(line: str) -> None:
    ChatExpression(line=line).write()
