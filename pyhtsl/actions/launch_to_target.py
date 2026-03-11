from typing import Self, final

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import HousingType
from ..stats.stat import Stat
from ..types import ALL_LOCATIONS

__all__ = ('launch_to_target',)


@final
class LaunchToTargetExpression(Expression):
    coordinates: str | None
    location: ALL_LOCATIONS
    strength: Stat | int

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
        strength: Stat | int = 2,
    ) -> None:
        self.coordinates = coordinates
        self.location = location
        self.strength = strength

    def into_htsl(self) -> str:
        line = f'launchTarget {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        else:
            line += f' {self.inline_quoted("~ ~ ~")}'
        line += f' {self.strength}'
        return line

    def cloned(self) -> Self:
        return self.__class__(
            coordinates=self.coordinates,
            location=self.location,
            strength=self.strength,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, LaunchToTargetExpression):
            return False
        return (
            self.coordinates == other.coordinates
            and self.location == other.location
            and self.strength == other.strength
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.location} strength={self.strength}>'


# TODO probably actually create Location class that has the coordinates and type
def launch_to_target(
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
    strength: Stat | int = 2,
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
    LaunchToTargetExpression(
        coordinates=resolved_coordinates,
        location=location,
        strength=strength,
    ).write()
