from collections.abc import Callable

from ..container import get_current_container
from .function import Function
from .goto import goto

__all__ = ('create_function',)


def create_function(
    name: str,
    *,
    force_create: bool | None = None,
    run_right_now: bool = False,
) -> Callable[[Callable[[], None]], Function[Callable[[], None]]]:
    def decorator(func: Callable[[], None]) -> Function[Callable[[], None]]:
        def callback() -> None:
            goto(container='function', name=name, add_to_front=True)
            create = (
                force_create
                if force_create is not None
                else (func.__module__ == '__main__')
            ) or (not get_current_container().is_global)
            if create:
                goto(container='function', name=name)
                func()

        function = Function(name=name, callback=callback)
        if run_right_now:
            callback()
        else:
            get_current_container().registered_functions.append(function)

        return function

    return decorator
