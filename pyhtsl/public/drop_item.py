from ..writer import WRITER, LineType
from ..types import ALL_LOCATIONS
from .item import Item

from typing import Optional


__all__ = (
    'drop_item',
)


def drop_item(
    item: Item | str,
    coordinates: Optional[
        tuple[float, float, float]  # (x, y, z)
        | tuple[str, str, str]  # (~x, ~y, ~z)
        | tuple[float, float, float, float, float]  # (x, y, z, yaw, pitch)
        | tuple[str, str, str, float, float]  # (~x, ~y, ~z, yaw, pitch)
        | str  # custom string
    ],
    location: ALL_LOCATIONS = 'custom_coordinates',
    drop_naturally: bool = False,
    disable_item_merging: bool = False,
    prioritize_player: bool = False,
    fallback_to_inventory: bool = False,
) -> None:
    if isinstance(item, Item):
        name = item.save()
    else:
        name = item
    line = f'dropItem "{name}"'
    if location == 'custom_coordinates':
        if coordinates is None:
            raise ValueError('coordinates must be provided when location is custom_coordinates')
        if isinstance(coordinates, tuple):
            coordinates = ' '.join(map(str, coordinates))
        line += f' "{coordinates}"'
    else:
        line += ' "~ ~ ~"'
    line += f' {str(drop_naturally).lower()} {str(disable_item_merging).lower()} {str(prioritize_player).lower()} {str(fallback_to_inventory).lower()}'
    WRITER.write(
        line,
        LineType.miscellaneous,
    )
