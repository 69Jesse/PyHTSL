from ..writer import WRITER

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
    WRITER.write(f'goto {container} "{name}"')
