from ..write import write

from typing import Literal, Optional


__all__ = (
    'set_compass_target',
)


# TODO proper overload
def set_compass_target(
    location: Literal[
        'house_spawn',
        'current_location',
        'invokers_location',
        'custom_coordinates',
    ] = 'invokers_location',
    coordinates: Optional[str] = None
) -> None:
    line = f'compassTarget "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        line += f' "{coordinates}"'
    write(line)
