from ..condition.base_condition import BaseCondition

from typing import final, Literal


__all__ = ('RequiredGamemode',)


@final
class RequiredGamemode(BaseCondition):
    gamemode: str

    def __init__(
        self,
        gamemode: Literal['adventure', 'survival', 'creative'],
    ) -> None:
        self.gamemode = gamemode

    def create_line(self) -> str:
        return f'gamemode {self.gamemode}'
