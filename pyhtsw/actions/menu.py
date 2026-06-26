from collections.abc import Callable, Sequence
from typing import Any, ClassVar, Literal

from ..block import NamedBlock
from ..container import get_current_container
from ..importable import MenuImportable, MenuSlot, XYCheck
from ..utils.caller import caller_module
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

    __htsw_importable__: ClassVar['MenuImportable']

    def __init_subclass__(cls, size: MenuSize) -> None:
        super().__init_subclass__()
        if not 1 <= size <= 6:
            raise ValueError(f'Menu "{cls.__name__}" size must be between 1 and 6.')
        cls.__htsw_name__ = cls.__name__
        cls.__htsw_size__ = size

        importable = MenuImportable(
            name=cls.__name__,
            size=size,
            slots=[],
            menu_cls=cls,
        )
        importable.module = caller_module()
        cls.__htsw_importable__ = importable

        for value in vars(cls).values():
            if not isinstance(value, _Element):
                continue
            cls._add_slot(value.item, value.x, value.y, value.xy_check, value.func)

        get_current_container().register_importable(importable)

    @classmethod
    def _add_slot(
        cls,
        item: 'Item | type[Item]',
        x: MenuAxis,
        y: MenuAxis,
        xy_check: XYCheck | None,
        func: Callable[..., Any],
    ) -> None:
        block = NamedBlock(f'{cls.__name__} slot', callback=func)
        get_current_container().add_block(block)
        cls.__htsw_importable__.slots.append(
            MenuSlot(item=item, x=x, y=y, xy_check=xy_check, block=block),
        )

    @classmethod
    def add_element(
        cls,
        *,
        item: 'Item | type[Item]',
        x: MenuAxis = None,
        y: MenuAxis = None,
        xy_check: XYCheck | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Add a slot to an already-defined menu (e.g. inside a loop). Mirrors
        `@Menu.element`, but registers immediately on the class instead of being
        collected from the class body."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            cls._add_slot(item, x, y, xy_check, func)
            return func

        return decorator
