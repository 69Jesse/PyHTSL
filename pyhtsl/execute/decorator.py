from collections.abc import Callable

from ..expression.expression import Expression
from ..utils.callback import call_with_optional_arg
from .context import ExecutionContext
from .expressions.run_execution_expression import CallbackType

__all__ = (
    'execute',
    'run_saved_execution_contexts',
)


_saved_execution_contexts: list[tuple[ExecutionContext, CallbackType]] = []


def execute(
    *,
    ignore_action_limits: bool = False,
    allow_nested_expressions: bool = False,
    verbose: bool = False,
    expression_callback: Callable[[Expression], None] | None = None,
    pause_multiplier: float = 1.0,
    volume_multiplier: float = 0.1,
) -> Callable[[CallbackType], ExecutionContext]:
    def decorator(callback: CallbackType) -> ExecutionContext:
        context = ExecutionContext(
            ignore_action_limits=ignore_action_limits,
            allow_nested_expressions=allow_nested_expressions,
            verbose=verbose,
            expression_callback=expression_callback,
            pause_multiplier=pause_multiplier,
            volume_multiplier=volume_multiplier,
        )
        _saved_execution_contexts.append((context, callback))
        return context

    return decorator


def run_saved_execution_contexts() -> None:
    while _saved_execution_contexts:
        context, callback = _saved_execution_contexts.pop(0)
        with context:
            call_with_optional_arg(callback, context, noun='callback')
