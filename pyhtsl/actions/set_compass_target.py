from typing import Self, final

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import HousingType
from ..types import ALL_LOCATIONS

__all__ = ('set_compass_target',)


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


# TODO proper overload
def set_compass_target(
    coordinates: tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ]
    | str
    | None = None,
    location: ALL_LOCATIONS = 'custom_coordinates',
) -> None:
    resolved_coordinates: str | None = None
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError(
                'coordinates must be provided when location is custom_coordinates'
            )
        if isinstance(coordinates, tuple):
            resolved_coordinates = ' '.join(map(str, coordinates))
        else:
            resolved_coordinates = coordinates
    SetCompassTargetExpression(
        coordinates=resolved_coordinates, location=location
    ).write()
