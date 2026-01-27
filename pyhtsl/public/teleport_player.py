from ..checkable import Checkable
from ..expression.housing_type import HousingType
from ..writer import WRITER, LineType
from ..types import ALL_LOCATIONS


__all__ = ('teleport_player',)


# TODO proper overload
# TODO probably actually create Location class that has the coordinates and type
def teleport_player(
    coordinates: tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ]
    | tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ]
    | str
    | None,
    location: ALL_LOCATIONS = 'custom_coordinates',
    prevent_teleport_inside_block: bool = False,
) -> None:
    line = f'tp "{location}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError(
                'coordinates must be provided when location is custom_coordinates'
            )
        if isinstance(coordinates, tuple):
            coordinates = ' '.join(
                map(
                    lambda x: x._as_string(include_fallback_value=False)
                    if isinstance(x, Checkable)
                    else str(x),
                    coordinates,
                )
            )
        line += f' "{coordinates}"'
    else:
        line += ' "~ ~ ~"'
    line += f' {str(prevent_teleport_inside_block).lower()}'
    WRITER.write(
        line,
        LineType.miscellaneous,
    )
