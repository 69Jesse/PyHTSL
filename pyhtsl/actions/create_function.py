from collections.abc import Callable
from typing import ParamSpec

from ..container import get_current_container
from .function import Function
from .goto import goto

__all__ = (
    'rename',
    'create_function',
)


ANNOTATION_EXAMPLE: str = (
    'Example:'
    "\n\n@create_function('My Function')"
    "\n@rename(p='player', g='global', t='team')"
    '\ndef my_function(p: PlayerStat, g: GlobalStat, t: TeamStat) -> None:'
    '\n    ...'
    '\n'
)


P = ParamSpec('P')
F = Callable[P, None]


def rename(**names: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        renamed_stats: dict[str, str] = getattr(func, '__pyhtsl_renamed_stats__', {})
        renamed_stats |= names
        func.__pyhtsl_renamed_stats__ = renamed_stats  # type: ignore
        return func

    return decorator


def create_function(
    name: str,
    *,
    force_create: bool | None = None,
    run_right_now: bool = False,
) -> Callable[[F], Function[F]]:
    def decorator(func: F) -> Function[F]:
        def callback() -> None:
            goto(container='function', name=name, add_to_front=True)  # pyright: ignore[reportCallIssue]
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
