"""End-to-end htsw project export: import.json structure, file layout,
pretty snbt, menu slot resolution, and item references."""

import json
import tempfile
from pathlib import Path

from pyhtsw import (
    NPC,
    Container,
    Item,
    Menu,
    Region,
    chat,
    create_event,
    create_function,
    give_item,
    set_projects_folder,
)

tmp = Path(tempfile.mkdtemp())
set_projects_folder(tmp)

with Container() as container:

    class MagicWand(Item, key='blaze_rod', name='&aMagic Wand'):
        @Item.right_click
        def on_right() -> None:
            chat('used the wand')

    class Border(Item, key='black_stained_glass_pane', name=' '):
        pass

    class Shop(Menu, size=6):
        @Menu.element(item=Border, x=0)
        def _border() -> None:
            pass

        @Menu.element(item=Border, xy_check=lambda x, y: (x + y) % 2 == 0)
        def _checker() -> None:
            pass

        @Menu.element(item=MagicWand, x=3, y=4)
        def buy() -> None:
            chat('bought')

    class Spawn(Region, bounds=((0, 100, 0), (10, 110, 10))):
        @Region.on_enter
        def enter() -> None:
            chat('entered')

    class Merchant(
        NPC,
        pos=(1.5, 64, 2.5),
        skin='Steve',
        look_at_players=True,
        equipment=NPC.Equipment(hand=MagicWand),
    ):
        @NPC.right_click
        def right() -> None:
            chat('hello')

    @create_function('Tick', repeat_ticks=20, icon=MagicWand)
    def tick() -> None:
        chat('tick')

    @create_event('Player Join')
    def join() -> None:
        give_item(MagicWand)


container.export('Export Test')

root = tmp / 'export-test'
data = json.loads((root / 'import.json').read_text())

# functions
assert data['functions'][0]['name'] == 'Tick'
assert data['functions'][0]['repeatTicks'] == 20
assert data['functions'][0]['icon'] == {'item': 'minecraft:blaze_rod'}
assert data['functions'][0]['actions'] == 'functions/tick.htsl'
assert (root / 'functions' / 'tick.htsl').exists()

# events
assert data['events'][0] == {
    'event': 'Player Join',
    'actions': 'events/player-join.htsl',
}
# the declared item is referenced by name from the action
assert 'giveItem "MagicWand"' in (root / 'events' / 'player-join.htsl').read_text()

# items: declared subclasses become items[] entries; class name is the reference
items = {entry['name']: entry for entry in data['items']}
assert items['MagicWand']['nbt'] == 'items/magicwand.snbt'
assert items['MagicWand']['rightClickActions'] == 'items/magicwand/right.htsl'
assert 'leftClickActions' not in items['MagicWand']
assert 'rightClickActions' not in items['Border']

# region
region = data['regions'][0]
assert region['name'] == 'Spawn'
assert region['bounds'] == {
    'from': {'x': 0, 'y': 100, 'z': 0},
    'to': {'x': 10, 'y': 110, 'z': 10},
}
assert region['onEnterActions'] == 'regions/spawn/enter.htsl'

# npc
npc = data['npcs'][0]
assert npc['name'] == 'Merchant'
assert npc['pos'] == {'x': 1.5, 'y': 64, 'z': 2.5}
assert npc['skin'] == 'Steve'
assert npc['lookAtPlayers'] is True
assert npc['equipment'] == {'hand': 'items/magicwand.snbt'}

# menu: x=0 fills the whole top row, the checkerboard fills (x+y) even cells,
# and the explicit (3, 4) -> slot 31 overrides whatever was there.
menu = data['menus'][0]
assert menu['size'] == 6
slots = {entry['slot']: entry for entry in menu['slots']}
assert set(range(9)).issubset(slots)  # row 0 fully filled
assert slots[31]['nbt'] == 'items/magicwand.snbt'
assert slots[31]['actions'] == 'menus/shop/slot-3-4.htsl'
assert slots[10]['nbt'] == 'items/border.snbt'  # (1,1) -> checkerboard

# pretty snbt is indented
snbt = (root / 'items' / 'magicwand.snbt').read_text()
assert '\n    id: "minecraft:blaze_rod"' in snbt
