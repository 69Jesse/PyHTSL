from typing import Self, final

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import HousingType
from ..types import ALL_LOCATIONS

__all__ = ('teleport_player',)


@final
class TeleportPlayerExpression(Expression):
    coordinates: str | None
    location: ALL_LOCATIONS
    prevent_teleport_inside_block: bool

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
        prevent_teleport_inside_block: bool = False,
    ) -> None:
        self.coordinates = coordinates
        self.location = location
        self.prevent_teleport_inside_block = prevent_teleport_inside_block

    def into_htsl(self) -> str:
        line = f'tp {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        else:
            line += f' {self.inline_quoted("~ ~ ~")}'
        line += f' {self.inline(self.prevent_teleport_inside_block)}'
        return line

    def cloned(self) -> Self:
        return self.__class__(
            coordinates=self.coordinates,
            location=self.location,
            prevent_teleport_inside_block=self.prevent_teleport_inside_block,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, TeleportPlayerExpression):
            return False
        return (
            self.coordinates == other.coordinates
            and self.location == other.location
            and self.prevent_teleport_inside_block == other.prevent_teleport_inside_block
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.location} {self.coordinates}>'


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
    resolved_coordinates: str | None = None
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError(
                'coordinates must be provided when location is custom_coordinates'
            )
        if isinstance(coordinates, tuple):
            resolved_coordinates = ' '.join(
                x.into_inside_string(include_fallback_value=False)
                if isinstance(x, Checkable)
                else str(x)
                for x in coordinates
            )
        else:
            resolved_coordinates = coordinates
    TeleportPlayerExpression(
        coordinates=resolved_coordinates,
        location=location,
        prevent_teleport_inside_block=prevent_teleport_inside_block,
    ).write()
