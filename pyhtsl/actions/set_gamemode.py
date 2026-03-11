from ..types import ALL_GAMEMODES
from ..writer import WRITER, LineType

__all__ = ('set_gamemode',)


def set_gamemode(
    gamemode: ALL_GAMEMODES,
) -> None:
    WRITER.write(
        f'gamemode {gamemode}',
        LineType.miscellaneous,
    )
