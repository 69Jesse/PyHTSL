from typing import TYPE_CHECKING

from ..types import GOTO_CONTAINER
from ..writer import WRITER, LineType

__all__ = ('goto',)


def _goto(
    container: GOTO_CONTAINER,
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
        container: GOTO_CONTAINER,
        name: str,
    ) -> None: ...
else:
    goto = _goto
