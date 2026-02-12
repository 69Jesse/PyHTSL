from typing import Literal

from ..writer import WRITER, LineType

__all__ = ('set_gamemode',)


def set_gamemode(
    gamemode: Literal['adventure', 'survival', 'creative'],
) -> None:
    WRITER.write(
        f'gamemode {gamemode}',
        LineType.miscellaneous,
    )
