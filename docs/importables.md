# Importables

Importables are the entities HTSW imports: functions, events, items, regions,
menus, NPCs, teams, groups and commands. See htsw's
`language/src/importjson/schemaSpec.ts` for the underlying import.json schema.

**The class declares, the string refers.** The kinds that own a single action
list (`@function`, `@command`, `@event`) are decorators; the rest are declared
by their constructors. Each declaration is a **value** — a `Function`, `Menu`,
`Region`, `Item`, ... — that you pass to actions, and that answers for its own
declaration:

```python
shop = Menu('Magic Shop', 6)

shop.name  # 'Magic Shop'
shop.size  # 6
```

Anything that already exists in the house without a declaration is referred to
by its plain name string — `set_player_team('Red')`, `trigger_function('greet')`,
`WithinRegion('Hand Placed')`. Declaring the same kind and name twice raises.

Every field of a declaration reads back off the value, and can be set on it
afterwards. `value.importable` is the declaration itself, for the rare case you
want the raw `import.json` entry.

## Functions

```python
from pyhtsw import Item, chat, function


@function('Tick', repeat_ticks=20, icon=Item('clock'))
def tick() -> None:
    chat('one second passed')
```

- `repeat_ticks` runs the function on an interval (optional). It is part of
  the function's definition, so the project is the source of truth for it:
  re-importing a looping function without `repeat_ticks` stops the loop in
  the house.
- `icon` is an `Item` (optional).

A house may hold **200 functions** in total, so a function is worth declaring
only when the actions have to be one shared thing. A menu slot or command whose
whole body triggers a single-use function should hold the actions itself
instead; an item's behaviour should always be a function. See
[Inlining](./inlining.md).

## Events

```python
from pyhtsw import event, chat


@event('player_join')
def on_join() -> None:
    chat('&aSomeone joined!')
```

`@event` returns an `Event` value, the way `@function` returns a
`Function`. Housing fires it, so — like a `Command` — it cannot be triggered
from HTSL; the value is there to name the event and to be re-exported.

The event name is typed to the 18 htsw events (`player_join`, `player_quit`,
`player_death`, `player_kill`, `player_respawn`, `group_change`,
`pvp_state_change`, `fish_caught`, `player_enter_portal`, `player_damage`,
`player_block_break`, `start_parkour`, `complete_parkour`, `player_drop_item`,
`player_pick_up_item`, `player_change_held_item`, `player_toggle_sneak`,
`player_toggle_flight`).

## Items, Regions, NPCs, Menus

These four own action lists — clicks, region enter/exit — so they are declared
by a call and their handlers are attached to the value it returns. Handlers are
callables that take **0 args, or 1 arg** that receives the value they belong to.

Each takes its handlers as keyword arguments, or as decorators afterwards:

| Importable | Decorators | Keyword shorthands |
|---|---|---|
| `Item` | `@item.on_left_click`, `@item.on_right_click`, `@item.on_click` | `on_left_click=`, `on_right_click=`, `on_click=` |
| `Region` | `@region.on_enter`, `@region.on_exit` | `on_enter=`, `on_exit=` |
| `NPC` | `@npc.on_left_click`, `@npc.on_right_click`, `@npc.on_click` | `on_left_click=`, `on_right_click=`, `on_click=` |
| `Menu` | `@menu.add_element(item, slot=)` | — |

```python
from pyhtsw import Item, chat


# Decorator form
wand = Item('blaze_rod', name='&dWand')


@wand.on_left_click
def cast() -> None:
    chat('zap')


@wand.on_right_click
def block() -> None:
    chat('block')
```

```python
# Keyword shorthand
def cast() -> None:
    chat('zap')


wand = Item('blaze_rod', name='&dWand', on_left_click=cast)
```

Because these are ordinary calls, any of them can be built in a loop, and a
handler closes over the loop variable through an ordinary function scope
instead of a default-argument dance.

### Item

`Item(...)` builds a value; `.declare()` declares it as an `items[]` entry up
front, so actions reference it by name and htsw lists it in the Project view. An
item given a click handler declares itself either way. See
[Items](./items.md) for the full field list and how names are derived.

```python
from pyhtsw import Item, chat, give_item

wand = Item('blaze_rod', name='&dWand').declare()


@wand.on_click
def cast() -> None:
    chat('zap')


give_item(wand)
```

- `.declare(name)` overrides the derived htsw name; `.declare()` derives it
  from the display name with formatting stripped (`&dWand` -> `Wand`), falling
  back to the vanilla item title when the item has no display name.
  It returns the item, so it chains off the constructor.
- Two items that render the same SNBT are one item to htsw, so the second one
  shares the first's entry rather than registering a duplicate.

### Region

```python
from pyhtsw import Region, chat


spawn = Region('Spawn Zone', ((0, 60, 0), (16, 80, 16)))


@spawn.on_enter
def entered() -> None:
    chat('&aentered spawn')


@spawn.on_exit
def left() -> None:
    chat('&7left spawn')
```

- `bounds` is `((x, y, z), (x, y, z))` — the from/to corners — and is
  **required**: htsw's schema marks the field required, so a declared region
  cannot be placed in-game later. A region you built in-game is referred to by
  its name string instead of being declared.
- `region.corners(a, b)` sets `bounds` from two opposite corners in either
  order, the way the in-game region tool hands them to you.
- `region.bounds` is readable and settable after declaration, so a region can be
  declared with placeholder bounds and corrected once the real coordinates are
  known.
- `region.attach('enter' | 'exit', handler)` is the non-decorator form, which is
  what a loop wants.

```python
pads = [Region(f'Pad {n}', ((n, 60, 0), (n + 1, 61, 1))) for n in range(3)]
```

`WithinRegion` takes the value, or a bare string for a region declared in-game:

```python
with IfAll(WithinRegion(spawn)):
    chat('&ain spawn')

with IfAll(WithinRegion('Hand Placed')):
    chat('&ein a region pyhtsw never declared')
```

### NPC

```python
from pyhtsw import NPC, Item, chat


helmet = Item('diamond_helmet')

guide = NPC(
    '&bVillage Guide',
    (10, 65, 10),
    skin='steve',
    look_at_players=True,
    hide_name_tag=False,
    equipment=NPC.Equipment(helmet=helmet),
)


@guide.on_right_click
def talk() -> None:
    chat('Welcome, traveler.')
```

- `name` is the NPC's displayed name (formatting codes allowed).
- `pos` is `(x, y, z)`.
- `skin` is one of `'steve'`, `'alex'`, `'players_skin'`.
- `left_click_redirect=True` makes a left click run the right-click actions.
- `NPC.Equipment(helmet=, chestplate=, leggings=, boots=, hand=)` — each an
  `Item`.
- A handler taking one argument receives the NPC it belongs to, so it can read
  its own name and position instead of closing over them.
- `npc.attach('left' | 'right' | 'both', handler)` is the non-decorator form.

NPCs generated from data are the common case:

```python
for enemy in ENEMIES:

    def strike(enemy=enemy) -> None:
        chat(f'You strike the {enemy.name}!')

    NPC(enemy.name, enemy.pos, skin='steve', on_click=strike)
```

#### on_click

Housing has no "either button" action list. A left click can only be pointed at
the right-click one, which is what `leftClickRedirect` does, so wanting an NPC
that just *responds to being clicked* costs two settings that have to agree.

`on_click` is that pair under one name: it fills the right-click list and turns
the redirect on.

```python
NPC('&aShopkeeper', (8, 65, 8), on_click=lambda: display_menu(SHOP))
```

It is mutually exclusive with `on_left_click`, `on_right_click` and
`left_click_redirect` — combining them is rejected, in whichever order they are
applied. Reach for the pair when the two buttons genuinely do different things,
and `on_click` when they don't.

### Menu

```python
from pyhtsw import Item, Menu, close_menu


filler = Item('gray_stained_glass_pane', name=' ')
confirm = Item('lime_dye', name='&aConfirm')

shop = Menu('Magic Shop', 6)
shop.fill(filler, xy_check=lambda x, y: (x + y) % 2 == 0)


@shop.add_element(confirm, x=5, y=4)
def buy() -> None:
    close_menu()
```

- `name` is the menu's displayed title. Formatting codes are **not** supported
  here; they render literally (`&aShop` shows as the text `&aShop`).
- `size` is typed `Literal[1, 2, 3, 4, 5, 6]` (rows). Menus are 9 columns wide.
- `menu.add_element(item, slot=, x=, y=, xy_check=)` adds a clickable slot; the
  item is positional, the placement keyword-only.
  - `slot` is the **flat** index Housing itself uses, `0`–`53`, shorthand for
    `x=slot // 9, y=slot % 9`. It also takes a sequence of indices. Pass either
    `slot=` or `x=`/`y=`, never both.
  - `x` is the **row**, `y` is the **column**. Each is `int | Sequence[int] |
    None`; `None` means every index on that axis.
  - Negative indices are allowed and resolved against the size at render time.
  - `xy_check=lambda x, y: ...` filters cells (e.g. a checkerboard pattern).
- `menu.place(item, slot=/x=/y=/xy_check=)` puts an item down with **no actions
  behind it** — decoration, or a label. It saves writing a handler whose whole
  body is `pass`.
- `menu.fill(item, xy_check=)` places `item` in every cell the check accepts
  (every cell when it is omitted). Later placements win, so fill first.
- `menu.distance_from_edge(x, y)` is how many cells in from the nearest border a
  cell is — `0` on the outer ring, `1` on the next — which is what makes a
  two-tone glass border one line each.
- Later elements override earlier ones per cell. Overriding a cell that a
  fully-explicit element (both `x` and `y` given) already set raises a `PyHTSWWarning` at the later placement.

A menu built from data — one page per shop category, one per reward tier — is
just the same call in a loop:

```python
from pyhtsw import Menu, give_item


def build_page(category) -> Menu:
    menu = Menu(f'Shop > {category.name}', 6)
    menu.fill(BLACK, xy_check=lambda x, y: menu.distance_from_edge(x, y) == 0)
    menu.fill(GRAY, xy_check=lambda x, y: menu.distance_from_edge(x, y) == 1)
    menu.place(INFO_ITEM, slot=4)

    for slot, entry in zip(SLOTS, category.items, strict=True):

        @menu.add_element(entry.item, slot=slot)
        def _buy(entry=entry) -> None:
            give_item(entry.item)

    return menu


PAGES = [build_page(category) for category in CATEGORIES]
```

Note the loop still binds `entry` through a default argument, because the `for`
body is not its own scope; lifting the loop into a helper that returns the
handler, or building one menu per function call, removes even that.

## Teams and Groups

Teams and groups hold no actions, so the constructor is the whole surface. Each
declares a `Team` / `Group` value the actions take directly, and the actions
also take a plain name string, so a declared team is used exactly like an
undeclared one that already exists in the house.

```python
from pyhtsw import Team, Group, set_player_team, change_player_group


Red = Team('Red', tag='RED', color='dark_red', friendly_fire=False)

VIP = Group(
    'VIP',
    tag='VIP',
    tag_shown_in_chat=True,
    color='gold',
    priority=5,
    allow=['fly', 'build', 'use_chests', 'tp'],
    deny=['ban', 'kick'],
    chat_speed='slow_1s',
    default_gamemode='adventure',
)

set_player_team(Red)
change_player_group(VIP)
Red.stat('kills').value += 1
```

- `tag` may contain only letters, digits and spaces.
- `color` is one of Housing's 14 named colours (`'dark_blue'` … `'yellow'`).
- `priority` is `0`–`20`.
- `allow=` / `deny=` are sequences of Housing's 51 permission names, typed as a
  `Literal` so a typo is a type error. A permission left out of both is
  **absent** from `import.json`, which is not the same as denying it. Naming one
  in both raises.
- `permissions={'fly': True, 'ban': False}` is the raw 1:1 form, accepted
  alongside `allow`/`deny` as an escape hatch.

As with every kind, each declared field reads back off the value itself —
`VIP.priority`, `VIP.color`, `Red.friendly_fire`. A field left out of the
declaration reads as `None`; `permissions` comes back as a read-only view.
Housing ships teams and groups that exist without a declaration; those are
referenced by their plain name string, everywhere a `Team` / `Group` value is
accepted:

```python
VIP.priority  # 5
Group('Plain').tag  # None
set_player_team('Red')  # the string names it, declared or not
TeamStat('kills', team='Red')
HasTeam('Red')
```

## Commands

A command owns a single action list, so it is a decorator like
`@function`.

```python
from pyhtsw import command, chat, teleport_player, Location


@command('warp', mode='self', required_priority=0, listed=True)
def warp() -> None:
    teleport_player(Location.custom(0, 100, 0))
    chat('&aWarped!')
```

- `mode` is `'self'` or `'targeted'`.
- `required_priority` is `0`–`20`.
- `listed` controls whether the command shows in the in-game list.

Housing has no trigger-command action, so unlike a `Function` the returned
`Command` cannot be called from other actions.

A command owning its own list is also why a command that only triggers one
single-use function should hold that function's actions directly — see
[Inlining](./inlining.md).

## Binding a house

`import.json` can carry a `houseUuid` that binds the project to one specific
house. It is opt-in and written only into the entry `import.json` — htsw
ignores the field in included files.

```python
import pyhtsw

pyhtsw.configure(house_uuid='3fcc64f4-0000-4000-8000-b517afa9958e')

# per container, which wins over the global one:
container.house_uuid = '3fcc64f4-0000-4000-8000-b517afa9958e'

# or per export, which wins over both:
container.export('MyHouse', house_uuid='3fcc64f4-0000-4000-8000-b517afa9958e')
```
