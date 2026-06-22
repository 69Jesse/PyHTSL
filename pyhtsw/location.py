from typing import ClassVar

from .actions.no_fallback_values import NoFallbackValues
from .checkable import Checkable
from .expression.housing_type import HousingType

__all__ = (
    'Location',
    'HouseSpawnLocation',
    'CurrentLocation',
    'InvokersLocation',
    'CustomLocation',
)

Coordish = Checkable | HousingType | float | int


class Location:
    """Base for the housing location types. Construct via the factory
    classmethods (``Location.custom`` / ``Location.house_spawn`` / ... ); the
    bare ``Location`` itself is never a valid value."""

    keyword: ClassVar[str]

    def render(self) -> tuple[str, str | None]:
        return type(self).keyword, None

    @staticmethod
    def custom(
        x: Coordish,
        y: Coordish,
        z: Coordish,
        pitch: Coordish | None = None,
        yaw: Coordish | None = None,
    ) -> 'CustomLocation':
        return CustomLocation(x, y, z, pitch, yaw)

    @staticmethod
    def house_spawn() -> 'HouseSpawnLocation':
        return HouseSpawnLocation()

    @staticmethod
    def invokers() -> 'InvokersLocation':
        return InvokersLocation()

    @staticmethod
    def current() -> 'CurrentLocation':
        return CurrentLocation()


class HouseSpawnLocation(Location):
    keyword = 'house_spawn'


class CurrentLocation(Location):
    keyword = 'current_location'


class InvokersLocation(Location):
    keyword = 'invokers_location'


class CustomLocation(Location):
    keyword = 'custom_coordinates'

    def __init__(
        self,
        x: Coordish,
        y: Coordish,
        z: Coordish,
        pitch: Coordish | None = None,
        yaw: Coordish | None = None,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.pitch = pitch
        self.yaw = yaw

    def render(self) -> tuple[str, str | None]:
        parts: list[Coordish] = [self.x, self.y, self.z]
        if self.pitch is not None or self.yaw is not None:
            parts.append(self.pitch if self.pitch is not None else 0)
            parts.append(self.yaw if self.yaw is not None else 0)
        with NoFallbackValues():
            coordinates = ' '.join(str(part) for part in parts)
        return type(self).keyword, coordinates


def resolve_location(location: Location) -> tuple[str, str | None]:
    if not isinstance(location, Location) or type(location) is Location:
        raise TypeError(
            'Expected a concrete Location, e.g. Location.custom(x, y, z), '
            'Location.house_spawn(), Location.invokers() or Location.current().',
        )
    return location.render()
