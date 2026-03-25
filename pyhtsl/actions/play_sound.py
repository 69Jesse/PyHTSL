from typing import TYPE_CHECKING, Self, final

from ..expression.expression import Expression
from ..types import ALL_LOCATIONS, ALL_SOUNDS
from ..utils.log import log

if TYPE_CHECKING:
    from ..execute.context import ExecutionContext

__all__ = ('play_sound',)


@final
class PlaySoundExpression(Expression):
    sound: ALL_SOUNDS
    volume: float
    pitch: float
    coordinates: str | None
    location: ALL_LOCATIONS

    def __init__(
        self,
        sound: ALL_SOUNDS,
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

    def raw_execute(self, context: 'ExecutionContext') -> None:
        from ..misc.sounds import play

        found = play(
            self.sound,
            volume=self.volume * context.volume_multiplier,
            pitch=self.pitch,
        )
        if not found:
            log(
                f'No sound found for \x1b[38;2;255;0;0m"{self.sound}"\x1b[0m, nothing will be played'
            )


# TODO proper overload
def play_sound(
    sound: ALL_SOUNDS,
    volume: float = 0.7,
    pitch: float = 1.0,
    coordinates: tuple[float, float, float] | str | None = None,
    location: ALL_LOCATIONS = 'invokers_location',
) -> None:
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
