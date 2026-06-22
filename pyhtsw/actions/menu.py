from collections.abc import Callable, Sequence
from typing import Any, ClassVar, Literal

from ..block import NamedBlock
from ..container import get_current_container
from ..importable import MenuImportable, MenuSlot, XYCheck
from .item import Item

__all__ = ('Menu',)

MenuSize = Literal[1, 2, 3, 4, 5, 6]
MenuAxis = int | Sequence[int] | None


class _Element:
    def __init__(
        self,
        func: Callable[..., Any],
        item: 'Item | type[Item]',
        x: MenuAxis,
        y: MenuAxis,
        xy_check: XYCheck | None,
    ) -> None:
        self.func = func
        self.item = item
        self.x = x
        self.y = y
        self.xy_check = xy_check


class Menu:
    COLS: ClassVar[int] = 9
    __htsw_name__: ClassVar[str | None] = None
    __htsw_size__: ClassVar[int]

    @classmethod
    def distance_from_edge(cls, x: int, y: int) -> int:
        """How many cells in from the nearest border (x/y are row/column).
        Cells on the outer edge return 0; the centre is the maximum."""
        return min(x, y, cls.__htsw_size__ - 1 - x, cls.COLS - 1 - y)

    @staticmethod
    def element(
        *,
        item: 'Item | type[Item]',
        x: MenuAxis = None,
        y: MenuAxis = None,
        xy_check: XYCheck | None = None,
    ) -> Callable[[Callable[..., Any]], _Element]:
        def decorator(func: Callable[..., Any]) -> _Element:
            return _Element(func, item, x, y, xy_check)

        return decorator

    def __init_subclass__(cls, size: MenuSize) -> None:
        super().__init_subclass__()
        if not 1 <= size <= 6:
            raise ValueError(f'Menu "{cls.__name__}" size must be between 1 and 6.')
        cls.__htsw_name__ = cls.__name__
        cls.__htsw_size__ = size

        container = get_current_container()
        slots: list[MenuSlot] = []
        for value in vars(cls).values():
            if not isinstance(value, _Element):
                continue
            block = NamedBlock(f'{cls.__name__} slot', callback=value.func)
            container.add_block(block)
            slots.append(
                MenuSlot(
                    item=value.item,
                    x=value.x,
                    y=value.y,
                    xy_check=value.xy_check,
                    block=block,
                ),
            )

        container.register_importable(
            MenuImportable(name=cls.__name__, size=size, slots=slots, menu_cls=cls),
        )
