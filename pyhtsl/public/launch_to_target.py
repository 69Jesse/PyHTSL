from ..writer import WRITER, LineType
from ..types import ALL_LOCATIONS
from ..stats.base_stat import BaseStat

from typing import Optional


__all__ = (
    'launch_to_target',
)


# TODO probably actually create Location class that has the coordinates and type
def launch_to_target(
    coordinates: Optional[
        tuple[float, float, float]  # (x, y, z)
        | tuple[str, str, str]  # (~x, ~y, ~z)
        | tuple[float, float, float, float, float]  # (x, y, z, yaw, pitch)
        | tuple[str, str, str, float, float]  # (~x, ~y, ~z, yaw, pitch)
        | str  # custom string
    ],
    location: ALL_LOCATIONS = 'custom_coordinates',
    strength: BaseStat | int = 2,
) -> None:
    line = f'launchTarget "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        if isinstance(coordinates, tuple):
            coordinates = ' '.join(map(str, coordinates))
        line += f' "{coordinates}"'
    else:
        line += ' "~ ~ ~"'
    line += f' {strength}'
    WRITER.write(
        line,
        LineType.miscellaneous,
    )
