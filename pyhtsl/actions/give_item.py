from typing import Self, final

from ..expression.expression import Expression
from ..types import _INVENTORY_SLOTS_PRETTY_NAME_MAPPING, INVENTORY_SLOTS
from .item import Item

__all__ = ('give_item',)


@final
class GiveItemExpression(Expression):
    item: Item | str
    allow_multiple: bool
    inventory_slot: str
    replace_existing_item: bool

    def __init__(
        self,
        item: Item | str,
        allow_multiple: bool = False,
        inventory_slot: str = 'first_slot',
        replace_existing_item: bool = False,
    ) -> None:
        self.item = item
        self.allow_multiple = allow_multiple
        self.inventory_slot = inventory_slot
        self.replace_existing_item = replace_existing_item

    def into_htsl(self) -> str:
        name = self.item.save() if isinstance(self.item, Item) else self.item
        return (
            f'giveItem {self.inline_quoted(name)} {self.inline(self.allow_multiple)}'
            f' {self.inline_quoted(self.inventory_slot)} {self.inline(self.replace_existing_item)}'
        )

    def cloned(self) -> Self:
        return self.__class__(
            item=self.item,
            allow_multiple=self.allow_multiple,
            inventory_slot=self.inventory_slot,
            replace_existing_item=self.replace_existing_item,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, GiveItemExpression):
            return False
        return (
            self.item == other.item
            and self.allow_multiple == other.allow_multiple
            and self.inventory_slot == other.inventory_slot
            and self.replace_existing_item == other.replace_existing_item
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.item} slot={self.inventory_slot}>'


def give_item(
    item: Item | str,
    allow_multiple: bool = False,
    inventory_slot: INVENTORY_SLOTS = 'first_slot',
    replace_existing_item: bool = False,
) -> None:
    inventory_slot = _INVENTORY_SLOTS_PRETTY_NAME_MAPPING.get(
        inventory_slot, inventory_slot
    )
    GiveItemExpression(
        item=item,
        allow_multiple=allow_multiple,
        inventory_slot=inventory_slot,
        replace_existing_item=replace_existing_item,
    ).write()
