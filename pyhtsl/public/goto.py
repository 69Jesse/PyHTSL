from ..write import write

from typing import Literal


__all__ = (
    'goto',
)


def goto(
    container: Literal[
        'function',
        'event',
        'command',
        'npc',
        'button',
        'pad',
    ],
    name: str,
) -> None:
    write(f'goto {container} "{name}"')
