from ..writer import WRITER, LineType
from ..types import INVENTORY_SLOTS, _INVENTORY_SLOTS_PRETTY_NAME_MAPPING
from .item import Item


__all__ = (
    'give_item',
)


def give_item(
    item: Item | str,
    allow_multiple: bool = False,
    inventory_slot: INVENTORY_SLOTS = 'first_slot',
    replace_existing_item: bool = False,
) -> None:
    inventory_slot = _INVENTORY_SLOTS_PRETTY_NAME_MAPPING.get(inventory_slot, inventory_slot)
    if isinstance(item, Item):
        name = item.save()
    else:
        name = item
    WRITER.write(
        f'giveItem "{name}" {str(allow_multiple).lower()} "{inventory_slot}" {str(replace_existing_item).lower()}',
        LineType.miscellaneous,
    )
