from ..writer import WRITER, LineType
from .function import Function


__all__ = (
    'trigger_function',
)


def trigger_function(
    function: Function | str,
    trigger_for_all_players: bool = False,
) -> None:
    function = function if isinstance(function, Function) else Function(function)
    WRITER.write(
        f'function "{function.name}" {str(trigger_for_all_players).lower()}',
        LineType.trigger_function,
    )
