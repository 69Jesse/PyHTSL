from ..condition.base_condition import BaseCondition
from .item import Item

from typing import final, Literal


__all__ = (
    'IsItem',
)


@final
class IsItem(BaseCondition):
    item: Item | str
    what_to_check: str
    where_to_check: str
    required_amount: str
    def __init__(
        self,
        item: Item | str,
        what_to_check: Literal['item_type', 'metadata'] = 'metadata',
        where_to_check: Literal['hand', 'armor', 'hotbar', 'inventory', 'cursor', 'crafting_grid', 'anywhere'] = 'anywhere',
        required_amount: Literal['any_amount', 'equal_or_greater_amount'] = 'any_amount',
    ) -> None:
        self.item = item
        self.what_to_check = what_to_check
        self.where_to_check = where_to_check
        self.required_amount = required_amount

    def create_line(self) -> str:
        if isinstance(self.item, Item):
            name = self.item.save()
        else:
            name = self.item
        return f'isItem "{name}" {self.what_to_check} {self.where_to_check} {self.required_amount}'
