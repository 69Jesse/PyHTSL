from public.no_fallback_values import NoFallbackValues
from ..checkable import Checkable
from ..expression.housing_type import HousingType
from ..writer import WRITER, LineType
from ..types import ALL_LOCATIONS
from .item import Item


__all__ = (
    'drop_item',
)


def drop_item(
    item: Item | str,
    coordinates: tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ] | tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ] | str | None,
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
    if coordinates is None:
        raise ValueError('coordinates must be provided when location is custom_coordinates')
    if isinstance(coordinates, tuple):
        with NoFallbackValues():
            coordinates = ' '.join(map(str, coordinates))
    line += f' "custom_coordinates" "{coordinates}"'
    line += f' {str(drop_naturally).lower()} {str(disable_item_merging).lower()} {str(prioritize_player).lower()} {str(fallback_to_inventory).lower()}'
    WRITER.write(
        line,
        LineType.miscellaneous,
    )
