from ..writer import WRITER, LineType
from ..types import ALL_LOCATIONS

from typing import Optional


__all__ = (
    'teleport_player',
)

# TODO proper overload
# TODO probably actually create Location class that has the coordinates and type
def teleport_player(
    coordinates: Optional[
        tuple[float, float, float]  # (x, y, z)
        | tuple[str, str, str]  # (~x, ~y, ~z)
        | tuple[float, float, float, float, float]  # (x, y, z, yaw, pitch)
        | tuple[str, str, str, float, float]  # (~x, ~y, ~z, yaw, pitch)
        | str  # custom string
    ],
    location: ALL_LOCATIONS = 'custom_coordinates',
    prevent_teleport_inside_block: bool = False,
) -> None:
    line = f'tp "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        if isinstance(coordinates, tuple):
            coordinates = ' '.join(map(str, coordinates))
        line += f' "{coordinates}"'
    else:
        line += ' "~ ~ ~"'
    line += f' {str(prevent_teleport_inside_block).lower()}'
    WRITER.write(
        line,
        LineType.miscellaneous,
    )
