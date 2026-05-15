from collections.abc import Callable

from ..block import FunctionBlock
from ..container import get_current_container
from .function import Function

__all__ = ('create_function',)


def create_function(
    name: str,
    *,
    run_right_now: bool = False,
) -> Callable[[Callable[[], None]], Function]:
    def decorator(callback: Callable[[], None]) -> Function:
        function = Function(name=name)
        block = FunctionBlock(function=function, callback=callback)

        get_current_container().add_block(block)
        if run_right_now:
            block.maybe_run_callback()

        return function

    return decorator
