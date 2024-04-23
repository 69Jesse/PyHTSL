from ..writer import WRITER, LineType
from .function import Function
from .player_stat import PlayerStat
from .global_stat import GlobalStat
from .team_stat import TeamStat

from typing import Optional, Iterable


__all__ = (
    'trigger_function',
)


def trigger_function(
    function: Function | str,
    trigger_for_all_players: bool = False,
    *,
    parameters: Optional[Iterable[PlayerStat | GlobalStat | TeamStat | int]] = None,
) -> None:
    function = function if isinstance(function, Function) else Function(function)
    if parameters is not None:
        parameters = tuple(parameters)
        if len(parameters) != len(function.parameters):
            raise TypeError(f'Expected {len(function.parameters)} parameters, got {len(parameters)}.')
        for i, (param, expected_param) in enumerate(zip(parameters, function.parameters)):
            if type(param) not in (PlayerStat, GlobalStat, TeamStat, int):
                raise TypeError(f'Parameter {i} must be either "{PlayerStat.__name__}", "{GlobalStat.__name__}", "{TeamStat.__name__}", or "{int.__name__}", not "{type(param).__name__}".')
            stat: PlayerStat | GlobalStat | TeamStat = expected_param.cls(name=expected_param.name)  # type: ignore
            stat.value = param
    WRITER.write(
        f'function "{function.name}" {str(trigger_for_all_players).lower()}',
        LineType.trigger_function,
    )
