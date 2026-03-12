from typing import Self, final

from ..checkable import Checkable
from ..expression.expression import Expression
from ..expression.housing_type import HousingType
from .item import Item
from .no_fallback_values import NoFallbackValues

__all__ = ('drop_item',)


@final
class DropItemExpression(Expression):
    item: Item | str
    coordinates: str
    drop_naturally: bool
    disable_item_merging: bool
    prioritize_player: bool
    fallback_to_inventory: bool

    def __init__(
        self,
        item: Item | str,
        coordinates: str,
        drop_naturally: bool = False,
        disable_item_merging: bool = False,
        prioritize_player: bool = False,
        fallback_to_inventory: bool = False,
    ) -> None:
        self.item = item
        self.coordinates = coordinates
        self.drop_naturally = drop_naturally
        self.disable_item_merging = disable_item_merging
        self.prioritize_player = prioritize_player
        self.fallback_to_inventory = fallback_to_inventory

    def into_htsl(self) -> str:
        name = self.item.save() if isinstance(self.item, Item) else self.item
        return (
            f'dropItem {self.inline_quoted(name)}'
            f' {self.inline_quoted("custom_coordinates")} {self.inline_quoted(self.coordinates)}'
            f' {self.inline(self.drop_naturally)} {self.inline(self.disable_item_merging)}'
            f' {self.inline(self.prioritize_player)} {self.inline(self.fallback_to_inventory)}'
        )

    def cloned(self) -> Self:
        return self.__class__(
            item=self.item,
            coordinates=self.coordinates,
            drop_naturally=self.drop_naturally,
            disable_item_merging=self.disable_item_merging,
            prioritize_player=self.prioritize_player,
            fallback_to_inventory=self.fallback_to_inventory,
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, DropItemExpression):
            return False
        return (
            self.item == other.item
            and self.coordinates == other.coordinates
            and self.drop_naturally == other.drop_naturally
            and self.disable_item_merging == other.disable_item_merging
            and self.prioritize_player == other.prioritize_player
            and self.fallback_to_inventory == other.fallback_to_inventory
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.item} at={self.coordinates}>'


def drop_item(
    item: Item | str,
    coordinates: tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ]
    | tuple[
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
        Checkable | HousingType,
    ]
    | str
    | None,
    drop_naturally: bool = False,
    disable_item_merging: bool = False,
    prioritize_player: bool = False,
    fallback_to_inventory: bool = False,
) -> None:
    if coordinates is None:
        raise ValueError(
            'coordinates must be provided when location is custom_coordinates'
        )
    if isinstance(coordinates, tuple):
        with NoFallbackValues():
            coordinates = ' '.join(map(str, coordinates))
    DropItemExpression(
        item=item,
        coordinates=coordinates,
        drop_naturally=drop_naturally,
        disable_item_merging=disable_item_merging,
        prioritize_player=prioritize_player,
        fallback_to_inventory=fallback_to_inventory,
    ).write()
