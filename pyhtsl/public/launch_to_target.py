from checkable import Checkable
from expression.housing_type import HousingType
from ..writer import WRITER, LineType
from ..types import ALL_LOCATIONS
from ..stats.base_stat import BaseStat


__all__ = (
    'launch_to_target',
)


# TODO probably actually create Location class that has the coordinates and type
def launch_to_target(
    coordinates: tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ] | tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ] | str | None,
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
