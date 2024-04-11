from ..writer import WRITER

from typing import TYPE_CHECKING, Literal


__all__ = (
    'goto',
)


if TYPE_CHECKING:
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
        ...
else:
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
        *,
        add_to_front: bool = False,
    ) -> None:
        WRITER.write(f'goto {container} "{name}"', add_to_front=add_to_front)
