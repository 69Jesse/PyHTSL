from ..writer import WRITER, LineType
from ..types import ALL_LOCATIONS

from typing import Optional


__all__ = (
    'set_compass_target',
)


# TODO proper overload
def set_compass_target(
    coordinates: Optional[tuple[float, float, float] | str] = None,
    location: ALL_LOCATIONS = 'invokers_location',
) -> None:
    line = f'compassTarget "{location}"'
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
