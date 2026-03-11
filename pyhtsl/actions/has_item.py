from typing import Literal, Self, final

from ..expression.condition.condition import Condition
from .item import Item

__all__ = ('HasItem',)


@final
class HasItem(Condition):
    item: Item | str
    what_to_check: str
    where_to_check: str
    required_amount: str

    def __init__(
        self,
        item: Item | str,
        what_to_check: Literal['item_type', 'metadata'] = 'metadata',
        where_to_check: Literal[
            'hand',
            'armor',
            'hotbar',
            'inventory',
            'cursor',
            'crafting_grid',
            'anywhere',
        ] = 'anywhere',
        required_amount: Literal[
            'any_amount', 'equal_or_greater_amount'
        ] = 'any_amount',
    ) -> None:
        self.item = item
        self.what_to_check = what_to_check
        self.where_to_check = where_to_check
        self.required_amount = required_amount

    def into_htsl_raw(self) -> str:
        if isinstance(self.item, Item):
            name = self.item.save()
        else:
            name = self.item

        required_amount = {
            'any_amount': 'Any Amount',
            'equal_or_greater_amount': 'Equal or Greater Amount',
        }[self.required_amount]
        return (
            f'hasItem {self.inline_quoted(name)} '
            f'{self.inline(self.what_to_check)} '
            f'{self.inline(self.where_to_check)} '
            f'{self.inline_quoted(required_amount)}'
        )

    def cloned_raw(self) -> Self:
        return self.__class__(
            item=self.cloned_or_same(self.item),
            what_to_check=self.what_to_check,
            where_to_check=self.where_to_check,
            required_amount=self.required_amount,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, HasItem):
            return False
        return (
            self.equals_or_eq(self.item, other.item)
            and self.what_to_check == other.what_to_check
            and self.where_to_check == other.where_to_check
            and self.required_amount == other.required_amount
        )

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}<item={self.item!r} '
            f'what_to_check={self.what_to_check} '
            f'where_to_check={self.where_to_check} '
            f'required_amount={self.required_amount} '
            f'inverted={self.inverted}>'
        )
