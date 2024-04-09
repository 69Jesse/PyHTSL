from ..write import write

from typing import Optional, Literal


__all__ = (
    'teleport_player',
)

# TODO proper overload
def teleport_player(
    location: Literal[
        'house_spawn',
        'current_location',
        'invokers_location',
        'custom_coordinates',
    ] = 'invokers_location',
    coordinates: Optional[str] = None
) -> None:
    line = f'tp "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        line += f' "{coordinates}"'
    write(line)
