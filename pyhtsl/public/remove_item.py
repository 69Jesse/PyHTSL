from ..writer import WRITER, LineType
from .item import Item


__all__ = (
    'remove_item',
)


def remove_item(
    item: Item | str,
) -> None:
    if isinstance(item, Item):
        name = item.save()
    else:
        name = item
    WRITER.write(
        f'removeItem "{name}"',
        LineType.miscellaneous,
    )
