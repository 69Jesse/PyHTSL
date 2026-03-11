from typing import Literal, Self, final

from ..expression.condition.condition import Condition

__all__ = ('RequiredGamemode',)


@final
class RequiredGamemode(Condition):
    gamemode: Literal['adventure', 'survival', 'creative']

    def __init__(
        self,
        gamemode: Literal['adventure', 'survival', 'creative'],
    ) -> None:
        self.gamemode = gamemode

    def into_htsl_raw(self) -> str:
        return f'gamemode {self.inline(self.gamemode)}'

    def cloned_raw(self) -> Self:
        return self.__class__(gamemode=self.gamemode)

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, RequiredGamemode):
            return False
        return self.gamemode == other.gamemode

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.gamemode} inverted={self.inverted}>'
