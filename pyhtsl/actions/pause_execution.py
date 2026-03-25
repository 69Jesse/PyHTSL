import time
from typing import Self, final

from pyhtsl.execute.context import ExecutionContext

from ..expression.expression import Expression

__all__ = ('pause_execution',)


@final
class PauseExecutionExpression(Expression):
    ticks: int

    def __init__(self, ticks: int = 20) -> None:
        self.ticks = ticks

    def into_htsl(self) -> str:
        return f'pause {self.inline(self.ticks)}'

    def cloned(self) -> Self:
        return self.__class__(ticks=self.ticks)

    def equals(self, other: object) -> bool:
        if not isinstance(other, PauseExecutionExpression):
            return False
        return self.ticks == other.ticks

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.ticks}>'

    def raw_execute(self, context: ExecutionContext) -> None:
        time.sleep((self.ticks / 20) * context.pause_multiplier)


def pause_execution(ticks: int = 20) -> None:
    PauseExecutionExpression(ticks=ticks).write()
