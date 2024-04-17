from ..writer import WRITER, LineType

from typing import TYPE_CHECKING, Literal


__all__ = (
    'goto',
)


def _goto(
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
    WRITER.write(
        f'goto {container} "{name}"',
        LineType.goto,
        add_to_front=add_to_front,
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
    goto = _goto
