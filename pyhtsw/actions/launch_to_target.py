from typing import Self, cast, final

from ..checkable import Checkable
from ..expression.expression import Expression
from ..location import Location, resolve_location
from ..types import ALL_LOCATIONS

__all__ = (
    'LaunchToTargetExpression',
    'launch_to_target',
)


@final
class LaunchToTargetExpression(Expression):
    coordinates: str | None
    location: ALL_LOCATIONS
    strength: Checkable | int

    def __init__(
        self,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'custom_coordinates',
        strength: Checkable | int = 2,
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
        line += f' {self.inline(self.strength)}'
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
            and self.equals_or_eq(self.strength, other.strength)
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.location} strength={self.strength}>'


def launch_to_target(
    location: Location,
    strength: Checkable | int = 2,
) -> None:
    keyword, coordinates = resolve_location(location)
    LaunchToTargetExpression(
        coordinates=coordinates,
        location=cast(ALL_LOCATIONS, keyword),
        strength=strength,
    ).write()
