from typing import Self, final

from ..expression.expression import Expression

__all__ = ('close_menu',)


@final
class CloseMenuExpression(Expression):
    def into_htsl(self) -> str:
        return 'closeMenu'

    def cloned(self) -> Self:
        return self.__class__()

    def equals(self, other: object) -> bool:
        return isinstance(other, CloseMenuExpression)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'


def close_menu() -> None:
    CloseMenuExpression().write()
