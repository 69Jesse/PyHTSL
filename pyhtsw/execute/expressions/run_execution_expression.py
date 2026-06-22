from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Self

from ...utils.callback import call_with_optional_arg
from .execution_expression import ExecutionExpression

if TYPE_CHECKING:
    from ..context import ExecutionContext


__all__ = (
    'CallbackType',
    'RunExecutionExpression',
)


type CallbackType = Callable[[], Any] | Callable[['ExecutionContext'], Any]


class RunExecutionExpression(ExecutionExpression):
    callback: CallbackType

    def __init__(self, callback: CallbackType) -> None:
        self.callback = callback

    def cloned(self) -> Self:
        return self.__class__(callback=self.callback)

    def equals(self, other: object) -> bool:
        if not isinstance(other, RunExecutionExpression):
            return False
        return self.callback == other.callback

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(callback={self.callback!r})'

    def raw_execute(self, context: 'ExecutionContext') -> None:
        call_with_optional_arg(self.callback, context, noun='callback')
