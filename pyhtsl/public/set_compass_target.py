from ..writer import WRITER, LineType
from .types import LOCATIONS

from typing import Optional


__all__ = (
    'set_compass_target',
)


# TODO proper overload
def set_compass_target(
    location: LOCATIONS = 'invokers_location',
    coordinates: Optional[str] = None
) -> None:
    line = f'compassTarget "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        line += f' "{coordinates}"'
    WRITER.write(
        line,
        LineType.miscellaneous,
    )
