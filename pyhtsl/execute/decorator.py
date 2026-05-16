from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..utils.callback import call_with_optional_arg
from .context import ExecutionContext
from .expressions.run_execution_expression import CallbackType

__all__ = (
    'execute',
    'run_saved_execution_contexts',
)


_saved_execution_contexts: list[tuple[ExecutionContext, CallbackType]] = []


def _execute(*args: Any, **kwargs: Any) -> Callable[[CallbackType], ExecutionContext]:
    def decorator(callback: CallbackType) -> ExecutionContext:
        context = ExecutionContext(*args, **kwargs)
        _saved_execution_contexts.append((context, callback))
        return context

    return decorator


if TYPE_CHECKING:
    execute = ExecutionContext().__init__
else:
    execute = _execute


def run_saved_execution_contexts() -> None:
    while _saved_execution_contexts:
        context, callback = _saved_execution_contexts.pop(0)
        with context:
            call_with_optional_arg(callback, context, noun='callback')
