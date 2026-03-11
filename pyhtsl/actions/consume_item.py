from typing import Self, final

from ..expression.expression import Expression

__all__ = ('consume_item',)


@final
class ConsumeItemExpression(Expression):
    def into_htsl(self) -> str:
        return 'consumeItem'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, ConsumeItemExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def consume_item() -> None:
    ConsumeItemExpression().write()
