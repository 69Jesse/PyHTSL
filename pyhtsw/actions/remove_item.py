from typing import Self, final

from ..expression.expression import Expression
from .item import Item, item_action_reference

__all__ = (
    'RemoveItemExpression',
    'remove_item',
)


@final
class RemoveItemExpression(Expression):
    item: Item | type[Item]

    def __init__(self, item: Item | type[Item]) -> None:
        self.item = item

    def into_htsl(self) -> str:
        name = item_action_reference(self.item)
        return f'removeItem {self.inline_quoted(name)}'

    def cloned(self) -> Self:
        return self.__class__(item=self.item)

    def equals(self, other: object) -> bool:
        if not isinstance(other, RemoveItemExpression):
            return False
        return self.item == other.item

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.item}>'


def remove_item(item: Item | type[Item]) -> None:
    RemoveItemExpression(item=item).write()
