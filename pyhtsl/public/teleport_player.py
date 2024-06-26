from ..writer import WRITER, LineType
from ..types import LOCATIONS

from typing import Optional


__all__ = (
    'teleport_player',
)

# TODO proper overload
def teleport_player(
    location: LOCATIONS = 'invokers_location',
    coordinates: Optional[str] = None
) -> None:
    line = f'tp "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        line += f' "{coordinates}"'
    WRITER.write(
        line,
        LineType.miscellaneous,
    )
