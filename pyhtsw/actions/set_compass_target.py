from typing import Self, cast, final

from ..expression.expression import Expression
from ..location import Location, resolve_location
from ..types import ALL_LOCATIONS

__all__ = (
    'SetCompassTargetExpression',
    'set_compass_target',
)


@final
class SetCompassTargetExpression(Expression):
    coordinates: str | None
    location: ALL_LOCATIONS

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
    ) -> None:
        self.coordinates = coordinates
        self.location = location

    def into_htsl(self) -> str:
        line = f'compassTarget {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        return line

    def cloned(self) -> Self:
        return self.__class__(coordinates=self.coordinates, location=self.location)

    def equals(self, other: object) -> bool:
        if not isinstance(other, SetCompassTargetExpression):
            return False
        return self.coordinates == other.coordinates and self.location == other.location

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.location} {self.coordinates}>'


def set_compass_target(location: Location) -> None:
    keyword, coordinates = resolve_location(location)
    SetCompassTargetExpression(
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
    ).write()
