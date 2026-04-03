from typing import TYPE_CHECKING, Self, final

from ..expression.expression import Expression

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext


__all__ = (
    'PauseExecutionExpression',
    'pause_execution',
)


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

    def raw_execute(self, context: 'ExecutionContext') -> None:
        from ..execute.signal import PauseSignal

        raise PauseSignal(self.ticks)


def pause_execution(ticks: int = 20) -> None:
    PauseExecutionExpression(ticks=ticks).write()
