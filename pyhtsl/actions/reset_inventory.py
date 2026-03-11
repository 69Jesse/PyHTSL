from typing import Self, final

from ..expression.expression import Expression

__all__ = ('reset_inventory',)


@final
class ResetInventoryExpression(Expression):
    def into_htsl(self) -> str:
        return 'resetInventory'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, ResetInventoryExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def reset_inventory() -> None:
    ResetInventoryExpression().write()
