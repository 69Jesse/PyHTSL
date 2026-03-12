from typing import Self, final

from ..expression.expression import Expression
from ..types import ALL_LOCATIONS, ALL_SOUNDS, ALL_SOUNDS_PRETTY_TO_RAW

__all__ = ('play_sound',)


@final
class PlaySoundExpression(Expression):
    sound: str
    volume: float
    pitch: float
    coordinates: str | None
    location: ALL_LOCATIONS

    def __init__(
        self,
        sound: str,
        volume: float = 0.7,
        pitch: float = 1.0,
        coordinates: str | None = None,
        location: ALL_LOCATIONS = 'invokers_location',
    ) -> None:
        self.sound = sound
        self.volume = volume
        self.pitch = pitch
        self.coordinates = coordinates
        self.location = location

    def into_htsl(self) -> str:
        line = f'sound {self.inline_quoted(self.sound)} {self.inline(self.volume)} {self.inline(self.pitch)} {self.inline_quoted(self.location)}'
        if self.location == 'custom_coordinates' and self.coordinates is not None:
            line += f' {self.inline_quoted(self.coordinates)}'
        return line

    def cloned(self) -> Self:
        return self.__class__(
            sound=self.sound,
            volume=self.volume,
            pitch=self.pitch,
            coordinates=self.coordinates,
            location=self.location,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, PlaySoundExpression):
            return False
        return (
            self.sound == other.sound
            and self.volume == other.volume
            and self.pitch == other.pitch
            and self.coordinates == other.coordinates
            and self.location == other.location
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.sound} vol={self.volume} pitch={self.pitch}>'


# TODO proper overload
def play_sound(
    sound: ALL_SOUNDS,
    volume: float = 0.7,
    pitch: float = 1.0,
    coordinates: tuple[float, float, float] | str | None = None,
    location: ALL_LOCATIONS = 'invokers_location',
) -> None:
    sound = ALL_SOUNDS_PRETTY_TO_RAW.get(sound, sound)  # pyright: ignore[reportAssignmentType]
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError(
                'coordinates must be provided when location is custom_coordinates'
            )
        if isinstance(coordinates, tuple):
            coordinates = ' '.join(map(str, coordinates))
    else:
        coordinates = None
    PlaySoundExpression(
        sound=sound,
        volume=volume,
        pitch=pitch,
        coordinates=coordinates,
        location=location,
    ).write()
