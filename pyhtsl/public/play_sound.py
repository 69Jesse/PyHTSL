from ..writer import WRITER, LineType
from ..types import ALL_SOUNDS, ALL_SOUNDS_PRETTY_TO_RAW, ALL_LOCATIONS


__all__ = (
    'play_sound',
)


# TODO proper overload
def play_sound(
    sound: ALL_SOUNDS,
    volume: float = 0.7,
    pitch: float = 1.0,
    coordinates: tuple[float, float, float] | str | None = None,
    location: ALL_LOCATIONS = 'invokers_location',
) -> None:
    sound = ALL_SOUNDS_PRETTY_TO_RAW.get(sound, sound)  # pyright: ignore[reportAssignmentType]
    line = f'sound "{sound}" {volume} {pitch} "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        if isinstance(coordinates, tuple):
            coordinates = ' '.join(map(str, coordinates))
        line += f' "{coordinates}"'
    WRITER.write(
        line,
        LineType.miscellaneous,
    )
