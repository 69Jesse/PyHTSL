from ..condition import TinyCondition

from typing import final, Literal


__all__ = (
    'RequiredGamemode',
)


@final
class RequiredGamemode(TinyCondition):
    gamemode: str
    def __init__(
        self,
        gamemode: Literal['adventure', 'survival', 'creative'],
    ) -> None:
        self.gamemode = gamemode

    def create_line(self) -> str:
        return f'isGamemode "{self.gamemode}"'
