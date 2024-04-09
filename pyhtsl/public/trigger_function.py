from ..write import write
from .function import Function


__all__ = (
    'trigger_function',
)


def trigger_function(
    function: Function | str,
    trigger_for_all_players: bool = False,
) -> None:
    function = function if isinstance(function, Function) else Function(function)
    write(f'function "{function.name}" {str(trigger_for_all_players).lower()}')
