from ..write import write

from typing import Literal


__all__ = (
    'set_gamemode',
)


def set_gamemode(
    gamemode: Literal['adventure', 'survival', 'creative'],
) -> None:
    write(f'gamemode {gamemode}')
