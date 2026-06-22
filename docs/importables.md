# Importables

Importables are the entities HTSW imports: functions, events, items, regions,
menus, and NPCs. PyHTSW declares them with decorators and class definitions; see
the [HTSW Importables reference](./htsw/importables.md) for the underlying
import.json schema.

## Functions

```python
from pyhtsw import create_function, chat


@create_function('Tick', repeat_ticks=20, icon=Clock)
def tick() -> None:
    chat('one second passed')
```

- `repeat_ticks` runs the function on an interval (optional).
- `icon` is an `Item` or `Item` subclass (optional).

## Events

```python
from pyhtsw import create_event, chat


@create_event('Player Join')
def on_join() -> None:
    chat('&aSomeone joined!')
```

The event name is typed to the 18 htsw events (`Player Join`, `Player Quit`,
`Player Death`, `Player Kill`, `Player Respawn`, `Group Change`,
`PvP State Change`, `Fish Caught`, `Player Enter Portal`, `Player Damage`,
`Player Block Break`, `Start Parkour`, `Complete Parkour`, `Player Drop Item`,
`Player Pick Up Item`, `Player Change Held Item`, `Player Toggle Sneak`,
`Player Toggle Flight`).

## Items, Regions, NPCs, Menus

These are declared as **subclasses** via `__init_subclass__`: the underlying
constructor arguments are passed as class keyword arguments. Defining the class
registers the importable; the class name is its htsw name.

### Click / enter / exit handlers

Each supports both a decorator form and a keyword shorthand. Handlers are
callables that take **0 args, or 1 arg** that receives the instance.

```python
from pyhtsw import Item, chat


# Decorator form
class Wand(Item, key='blaze_rod', name='&dWand'):
    @Item.left_click
    def cast(self) -> None:
        chat('zap')

    @Item.right_click
    def block(self) -> None:
        chat('block')
```

```python
# Keyword shorthand
def cast() -> None:
    chat('zap')


class Wand(Item, key='blaze_rod', name='&dWand', on_left_click=cast):
    pass
```

The handler shorthands per importable:

| Importable | Decorators | Keyword shorthands |
|---|---|---|
| `Item` | `@Item.left_click`, `@Item.right_click` | `on_left_click=`, `on_right_click=` |
| `Region` | `@Region.on_enter`, `@Region.on_exit` | `on_enter=`, `on_exit=` |
| `NPC` | `@NPC.left_click`, `@NPC.right_click` | `on_left_click=`, `on_right_click=` |

### Region

```python
from pyhtsw import Region, chat


class SpawnZone(Region, bounds=((0, 60, 0), (16, 80, 16))):
    @Region.on_enter
    def entered(self) -> None:
        chat('&aentered spawn')

    @Region.on_exit
    def left(self) -> None:
        chat('&7left spawn')
```

`bounds` is `((x, y, z), (x, y, z))` — the from/to corners.

### NPC

```python
from pyhtsw import NPC, Item, chat


class Helmet(Item, key='diamond_helmet'):
    pass


class Guide(
    NPC,
    pos=(10, 65, 10),
    skin='Steve',
    look_at_players=True,
    hide_name_tag=False,
    equipment=NPC.Equipment(helmet=Helmet),
):
    @NPC.right_click
    def talk(self) -> None:
        chat('Welcome, traveler.')
```

- `pos` is `(x, y, z)`.
- `skin` is one of `'Steve'`, `'Alex'`, `'Players Skin'`.
- `NPC.Equipment(helmet=, chestplate=, leggings=, boots=, hand=)` — each is an
  `Item` or `Item` subclass.

### Menu

```python
from pyhtsw import Menu, Item, chat, close_menu


class Filler(Item, key='gray_stained_glass_pane', name=' '):
    pass


class Confirm(Item, key='lime_dye', name='&aConfirm'):
    pass


class Shop(Menu, size=6):
    @Menu.element(item=Filler, xy_check=lambda x, y: (x + y) % 2 == 0)
    def checkerboard(self) -> None:
        pass  # decoration only, no actions

    @Menu.element(item=Confirm, x=5, y=4)
    def confirm(self) -> None:
        close_menu()
```

- `size` is **required** and typed `Literal[1, 2, 3, 4, 5, 6]` (rows). Menus are
  9 columns wide.
- `@Menu.element(item=, x=, y=, xy_check=)`:
  - `x` is the **row**, `y` is the **column**. Each is `int | Sequence[int] |
    None`; `None` means every index on that axis.
  - Negative indices are allowed and resolved against the size at render time.
  - `xy_check=lambda x, y: ...` filters cells (e.g. a checkerboard pattern).
  - An element body of just `pass` is decoration (no actions).
- Later elements override earlier ones per cell. Overriding a cell that a
  fully-explicit element (both `x` and `y` given) already set logs a warning.
