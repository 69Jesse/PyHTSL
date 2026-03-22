from collections.abc import Callable

from ..block import FunctionBlock
from ..container import get_current_container
from .function import Function

__all__ = ('create_function',)


def create_function(
    name: str,
    *,
    force_create: bool | None = None,
    run_right_now: bool = False,
) -> Callable[[Callable[[], None]], Function]:
    def decorator(func: Callable[[], None]) -> Function:
        def callback() -> None:
            create = (
                force_create
                if force_create is not None
                else (func.__module__ == '__main__')
            ) or (not get_current_container().is_global)
            if create:
                func()

        function = Function(name=name)
        block = FunctionBlock(function=function, callback=callback)

        get_current_container().blocks.append(block)
        if run_right_now:
            block.maybe_run_callback()

        return function

    return decorator
