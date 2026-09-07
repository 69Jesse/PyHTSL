from collections.abc import Callable, Sequence
from typing import Any, ClassVar, Literal

from pyhtsw.compiler.block import NamedBlock
from pyhtsw.compiler.container import get_current_container
from pyhtsw.compiler.importable import MenuImportable, MenuSlot, XYCheck
from pyhtsw.declarations.declared import Declared, declared_field, register_importable
from pyhtsw.declarations.item import Item
from pyhtsw.utils.warn import consumer_site

__all__ = ('Menu',)

MenuSize = Literal[1, 2, 3, 4, 5, 6]
MenuAxis = int | Sequence[int] | None
MenuSlotSpec = int | Sequence[int] | None

_COLS = 9


def _check_size(name: str, size: int) -> None:
    if not 1 <= size <= 6:
        raise ValueError(f'Menu "{name}" size must be between 1 and 6.')


def _slot_membership(
    name: str,
    slots: Sequence[int],
    rows: int,
    xy_check: XYCheck | None,
) -> XYCheck:
    from pyhtsw.compiler.importable import call_with_args

    resolved: set[int] = set()
    total = rows * _COLS
    for index in slots:
        normalised = index + total if index < 0 else index
        if not 0 <= normalised < total:
            raise ValueError(
                f'Menu "{name}": slot {index} is out of range for size {rows}.',
            )
        resolved.add(normalised)

    def check(row: int, column: int, menu: Any) -> bool:
        if row * _COLS + column not in resolved:
            return False
        return xy_check is None or bool(call_with_args(xy_check, row, column, menu))

    return check


class Menu(Declared):
    COLS: ClassVar[int] = _COLS
    __htsw_kind__ = 'menus'
    __htsw_factory__ = 'Menu'

    size: declared_field[int] = declared_field()

    def __init__(self, name: str, size: MenuSize) -> None:
        _check_size(name, size)
        super().__init__(name)
        self.__htsw_importable__ = register_importable(
            MenuImportable(name=name, size=size, slots=[], menu=self),
        )

    @property
    def declared(self) -> MenuImportable:
        importable = self.declaration()
        assert isinstance(importable, MenuImportable)
        return importable

    def distance_from_edge(self, x: int, y: int) -> int:
        """How many cells in from the nearest border (x/y are row/column).
        Cells on the outer edge return 0; the centre is the maximum."""
        return min(x, y, self.size - 1 - x, _COLS - 1 - y)

    def _add_slot(
        self,
        item: Item,
        x: MenuAxis,
        y: MenuAxis,
        xy_check: XYCheck | None,
        func: 'Callable[..., Any] | None',
    ) -> None:
        block: NamedBlock | None = None
        if func is not None:
            # The handler's own name, so an over-limit error points at the code
            # rather than at a coordinate that is only resolved much later.
            block = NamedBlock(
                f'{self.name} slot {getattr(func, "__name__", "?")}',
                callback=func,
                importable_kind='menus',
            )
            get_current_container().add_block(block)
        self.declared.slots.append(
            MenuSlot(
                item=item,
                x=x,
                y=y,
                xy_check=xy_check,
                block=block,
                site=consumer_site(),
            ),
        )

    def _placement(
        self,
        slot: MenuSlotSpec,
        x: MenuAxis,
        y: MenuAxis,
        xy_check: XYCheck | None,
    ) -> tuple[MenuAxis, MenuAxis, XYCheck | None]:
        name = self.name
        if slot is None:
            return x, y, xy_check
        if x is not None or y is not None:
            raise ValueError(f'Menu "{name}": pass either slot= or x=/y=, not both.')
        if isinstance(slot, int):
            return slot // _COLS, slot % _COLS, xy_check
        slots = tuple(slot)
        if not slots:
            raise ValueError(f'Menu "{name}": slot= was given an empty sequence.')
        return None, None, _slot_membership(name, slots, self.size, xy_check)

    def add_element(
        self,
        item: Item,
        *,
        slot: MenuSlotSpec = None,
        x: MenuAxis = None,
        y: MenuAxis = None,
        xy_check: XYCheck | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Add a clickable slot: `@menu.add_element(item, slot=28)`."""
        x, y, xy_check = self._placement(slot, x, y, xy_check)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._add_slot(item, x, y, xy_check, func)
            return func

        return decorator

    def place(
        self,
        item: Item,
        *,
        slot: MenuSlotSpec = None,
        x: MenuAxis = None,
        y: MenuAxis = None,
        xy_check: XYCheck | None = None,
    ) -> None:
        """Put an item in a slot with nothing behind it - decoration, or a
        label. Saves writing a handler whose whole body is `pass`."""
        x, y, xy_check = self._placement(slot, x, y, xy_check)
        self._add_slot(item, x, y, xy_check, None)

    def fill(
        self,
        item: Item,
        *,
        xy_check: XYCheck | None = None,
    ) -> None:
        """Place `item` in every cell `xy_check` accepts (every cell when it is
        omitted). Later placements win, so fill first and place on top after."""
        self._add_slot(item, None, None, xy_check, None)
