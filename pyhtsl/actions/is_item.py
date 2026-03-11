from typing import Self, final

from ..expression.condition.condition import Condition
from ..types import ITEM_CHECK_WHAT, ITEM_CHECK_WHERE, ITEM_REQUIRED_AMOUNT
from .item import Item

__all__ = ('IsItem',)


@final
class IsItem(Condition):
    item: Item | str
    what_to_check: ITEM_CHECK_WHAT
    where_to_check: ITEM_CHECK_WHERE
    required_amount: ITEM_REQUIRED_AMOUNT

    def __init__(
        self,
        item: Item | str,
        what_to_check: ITEM_CHECK_WHAT = 'metadata',
        where_to_check: ITEM_CHECK_WHERE = 'anywhere',
        required_amount: ITEM_REQUIRED_AMOUNT = 'any_amount',
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
        return (
            f'isItem {self.inline_quoted(name)} '
            f'{self.inline(self.what_to_check)} '
            f'{self.inline(self.where_to_check)} '
            f'{self.inline(self.required_amount)}'
        )

    def cloned_raw(self) -> Self:
        return self.__class__(
            item=self.cloned_or_same(self.item),
            what_to_check=self.what_to_check,
            where_to_check=self.where_to_check,
            required_amount=self.required_amount,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, IsItem):
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
