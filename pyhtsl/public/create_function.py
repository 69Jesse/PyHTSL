from ..writer import WRITER
from .goto import goto
from .function import Function
from ..stats.stat_parameter import StatParameter
from ..stats.player_stat import PlayerStat
from ..stats.global_stat import GlobalStat
from ..stats.team_stat import TeamStat

import inspect

from typing import Callable, ParamSpec


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
            ) or (not WRITER.get_container().is_global)
            if create:
                goto(container='function', name=name)
                func()

        function = Function(name=name, callback=callback)
        if run_right_now:
            callback()
        else:
            WRITER.get_container().registered_functions.append(function)

        return function

    return decorator
