from ..checkable import Checkable
from ..expression.housing_type import HousingType
from ..writer import WRITER, LineType
from ..types import ALL_LOCATIONS


__all__ = (
    'set_compass_target',
)


# TODO proper overload
def set_compass_target(
    coordinates: tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ] | str | None = None,
    location: ALL_LOCATIONS = 'custom_coordinates',
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
