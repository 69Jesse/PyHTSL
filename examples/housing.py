"""A small but complete htsw project: an item with a click action, a shop menu,
a spawn region, an NPC, a join event and a repeating function.

Running this writes a project folder into your htsw projects folder.
"""

from pyhtsw import (
    NPC,
    Item,
    Menu,
    Region,
    chat,
    create_event,
    create_function,
    display_menu,
    give_item,
)


class MagicWand(Item, key='blaze_rod', name='&aMagic Wand', lore='&7Right-click me'):
    @Item.right_click
    def on_right() -> None:
        chat('&dPoof!')


class Border(Item, key='black_stained_glass_pane', name=' '):
    pass


class Shop(Menu, size=6):
    # whole outer-ish decoration: fill the top row, then a checkerboard
    @Menu.element(item=Border, x=0)
    def _top() -> None:
        pass

    @Menu.element(item=Border, xy_check=lambda x, y: (x + y) % 2 == 0)
    def _checker() -> None:
        pass

    @Menu.element(item=MagicWand, x=2, y=4)
    def buy_wand() -> None:
        give_item(MagicWand)
        chat('&aYou bought the Magic Wand!')


class Spawn(Region, bounds=((0, 100, 0), (16, 120, 16))):
    @Region.on_enter
    def enter() -> None:
        chat('&aWelcome to spawn!')


class Shopkeeper(
    NPC,
    pos=(8.5, 100, 8.5),
    skin='Alex',
    look_at_players=True,
    on_right_click=lambda: display_menu(Shop),
):
    pass


@create_event('Player Join')
def on_join() -> None:
    give_item(MagicWand)
    chat('&eWelcome! Right-click the wand or visit the shopkeeper.')


@create_function('Heartbeat', repeat_ticks=200, icon=MagicWand)
def heartbeat() -> None:
    chat('&8The house hums quietly...')
