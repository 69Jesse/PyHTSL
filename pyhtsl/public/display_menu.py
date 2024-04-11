from ..writer import WRITER
from .menu import Menu


__all__ = (
    'display_menu',
)


def display_menu(
    menu: Menu | str,
) -> None:
    menu = menu if isinstance(menu, Menu) else Menu(menu)
    WRITER.write(f'displayMenu "{menu.name}"')
