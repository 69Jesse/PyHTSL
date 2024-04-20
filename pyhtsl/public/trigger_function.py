from ..writer import WRITER, LineType
from .function import Function
from .player_stat import PlayerStat
from .global_stat import GlobalStat
from .team_stat import TeamStat

from typing import Optional


__all__ = (
    'trigger_function',
)


def trigger_function(
    function: Function | str,
    trigger_for_all_players: bool = False,
    *,
    parameters: Optional[tuple[PlayerStat | GlobalStat | TeamStat | int, ...]] = None,
) -> None:
    function = function if isinstance(function, Function) else Function(function)
    if parameters is not None:
        if len(parameters) != len(function.parameters):
            raise TypeError(f'Expected {len(function.parameters)} parameters, got {len(parameters)}.')
        for i, (param, expected_param) in enumerate(zip(parameters, function.parameters)):
            if not isinstance(param, expected_param.cls) and not isinstance(param, int):
                raise TypeError(f'Expected parameter {i} to be of type "{expected_param.cls.__name__}", got "{param.__class__.__name__}".')
            stat: PlayerStat | GlobalStat | TeamStat = expected_param.cls(name=expected_param.name)
            stat.value = param
    WRITER.write(
        f'function "{function.name}" {str(trigger_for_all_players).lower()}',
        LineType.trigger_function,
    )
