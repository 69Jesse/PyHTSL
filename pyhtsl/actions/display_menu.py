from typing import Self, final

from ..expression.expression import Expression
from .menu import Menu

__all__ = ('display_menu',)


@final
class DisplayMenuExpression(Expression):
    menu: Menu

    def __init__(self, menu: Menu) -> None:
        self.menu = menu

    def into_htsl(self) -> str:
        return f'displayMenu {self.inline_quoted(self.menu.name)}'

    def cloned(self) -> Self:
        return self.__class__(menu=self.menu)

    def equals(self, other: object) -> bool:
        if not isinstance(other, DisplayMenuExpression):
            return False
        return self.menu.name == other.menu.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.menu.name}>'


def display_menu(menu: Menu | str) -> None:
    menu = menu if isinstance(menu, Menu) else Menu(menu)
    DisplayMenuExpression(menu=menu).write()
