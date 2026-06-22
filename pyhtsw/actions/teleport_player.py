from typing import Self, cast, final

from ..expression.expression import Expression
from ..location import Location, resolve_location
from ..types import ALL_LOCATIONS

__all__ = (
    'TeleportPlayerExpression',
    'teleport_player',
)


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
            and self.prevent_teleport_inside_block
            == other.prevent_teleport_inside_block
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.location} {self.coordinates}>'


def teleport_player(
    location: Location,
    prevent_teleport_inside_block: bool = False,
) -> None:
    keyword, coordinates = resolve_location(location)
    TeleportPlayerExpression(
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
        prevent_teleport_inside_block=prevent_teleport_inside_block,
    ).write()
