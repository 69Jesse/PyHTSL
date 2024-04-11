from ..writer import WRITER

from typing import Literal


__all__ = (
    'set_gamemode',
)


def set_gamemode(
    gamemode: Literal['adventure', 'survival', 'creative'],
) -> None:
    WRITER.write(f'gamemode {gamemode}')
