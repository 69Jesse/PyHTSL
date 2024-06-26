from ..writer import WRITER, LineType
from ..types import INVENTORY_SLOTS
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
    if isinstance(item, Item):
        name = item.save()
    else:
        name = item
    WRITER.write(
        f'giveItem "{name}" {str(allow_multiple).lower()} {inventory_slot} {str(replace_existing_item).lower()}',
        LineType.miscellaneous,
    )
