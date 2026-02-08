from typing import Literal, final

from ..condition.base_condition import BaseCondition

__all__ = ('RequiredGamemode',)


@final
class RequiredGamemode(BaseCondition):
    gamemode: str

    def __init__(
        self,
        gamemode: Literal['adventure', 'survival', 'creative'],
    ) -> None:
        self.gamemode = gamemode

    def into_htsl_raw(self) -> str:
        return f'gamemode {self.gamemode}'
