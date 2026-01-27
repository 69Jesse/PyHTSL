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
    create: bool | None = None,
    run_right_now: bool = False,
) -> Callable[[F], Function]:
    def decorator(func: F) -> Function:
        parameters: list[StatParameter] = []
        renamed_parameters: dict[str, str] = getattr(
            func, '__pyhtsl_renamed_stats__', {}
        )
        signature = inspect.signature(func)
        for param_name, raw_param in signature.parameters.items():
            annotation = raw_param.annotation
            if annotation is inspect.Parameter.empty:
                raise TypeError(
                    f'Parameter "{param_name}" must have an annotation. '
                    + ANNOTATION_EXAMPLE
                )
            if annotation not in (PlayerStat, GlobalStat, TeamStat):
                raise TypeError(
                    f'Parameter "{param_name}" must be either "{PlayerStat.__name__}", "{GlobalStat.__name__}", or "{TeamStat.__name__}", not "{annotation.__name__}". '
                    + ANNOTATION_EXAMPLE
                )
            param = StatParameter(
                name=renamed_parameters.get(param_name, param_name), cls=annotation
            )
            parameters.append(param)

        def callback() -> None:
            goto(container='function', name=name, add_to_front=True)  # type: ignore
            force = not WRITER.get_container().is_global
            if force or (
                create if create is not None else (func.__module__ == '__main__')
            ):
                goto(container='function', name=name)
                func(*(param.cls(name=param.name) for param in parameters))  # type: ignore

        function = Function(name=name, parameters=parameters, callback=callback)
        if run_right_now:
            callback()
        else:
            WRITER.get_container().registered_functions.append(function)
        return function

    return decorator
