from collections.abc import Callable
from typing import TYPE_CHECKING

from ..block import FunctionBlock
from ..container import get_current_container
from ..importable import FunctionImportable
from .function import Function

if TYPE_CHECKING:
    from .item import Item

__all__ = ('create_function',)


def create_function(
    name: str,
    *,
    repeat_ticks: int | None = None,
    icon: 'Item | type[Item] | None' = None,
) -> Callable[[Callable[[], None]], Function]:
    def decorator(callback: Callable[[], None]) -> Function:
        function = Function(name=name)
        block = FunctionBlock(function=function, callback=callback)

        container = get_current_container()
        container.add_block(block)
        container.register_importable(
            FunctionImportable(
                block,
                name=name,
                repeat_ticks=repeat_ticks,
                icon=icon,
            ),
        )
        return function

    return decorator
