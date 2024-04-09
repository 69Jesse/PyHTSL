from ..write import write

from typing import Literal, Optional


__all__ = (
    'play_sound',
)


# TODO proper overload
def play_sound(
    sound: str,
    volume: float = 0.7,
    pitch: float = 1.0,
    location: Literal[
        'house_spawn',
        'current_location',
        'invokers_location',
        'custom_coordinates',
    ] = 'invokers_location',
    coordinates: Optional[str] = None
) -> None:
    line = f'playSound "{sound}" {volume} {pitch} "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        line += f' "{coordinates}"'
    write(line)
