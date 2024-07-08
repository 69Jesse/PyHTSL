from ..writer import WRITER, LineType
from ..types import ALL_SOUNDS, ALL_SOUNDS_PRETTY_TO_RAW, ALL_LOCATIONS

from typing import Optional


__all__ = (
    'play_sound',
)


# TODO proper overload
def play_sound(
    sound: ALL_SOUNDS,
    volume: float = 0.7,
    pitch: float = 1.0,
    location: ALL_LOCATIONS = 'invokers_location',
    coordinates: Optional[str] = None
) -> None:
    sound = ALL_SOUNDS_PRETTY_TO_RAW.get(sound, sound)  # pyright: ignore[reportAssignmentType]
    line = f'playSound "{sound}" {volume} {pitch} "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        line += f' "{coordinates}"'
    WRITER.write(
        line,
        LineType.miscellaneous,
    )
