import hashlib
import json
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from .utils.kebab import into_kebab
from .utils.log import log

if TYPE_CHECKING:
    from .actions.item import Item
    from .actions.menu import Menu
    from .block import Block

__all__ = (
    'EVENTS',
    'EventName',
    'NpcSkin',
    'Coord',
    'Bounds',
)


HEADER = '// Generated with PyHTSW (https://github.com/69Jesse/PyHTSW)'

# A 0-arg handler (the importable has no runtime instance to hand back).
Handler = Callable[[], Any]

EVENTS: tuple[str, ...] = (
    'Player Join',
    'Player Quit',
    'Player Death',
    'Player Kill',
    'Player Respawn',
    'Group Change',
    'PvP State Change',
    'Fish Caught',
    'Player Enter Portal',
    'Player Damage',
    'Player Block Break',
    'Start Parkour',
    'Complete Parkour',
    'Player Drop Item',
    'Player Pick Up Item',
    'Player Change Held Item',
    'Player Toggle Sneak',
    'Player Toggle Flight',
)

EventName = Literal[
    'Player Join',
    'Player Quit',
    'Player Death',
    'Player Kill',
    'Player Respawn',
    'Group Change',
    'PvP State Change',
    'Fish Caught',
    'Player Enter Portal',
    'Player Damage',
    'Player Block Break',
    'Start Parkour',
    'Complete Parkour',
    'Player Drop Item',
    'Player Pick Up Item',
    'Player Change Held Item',
    'Player Toggle Sneak',
    'Player Toggle Flight',
]

NpcSkin = Literal['Steve', 'Alex', 'Players Skin']

Coord = tuple[float, float, float]
Bounds = tuple[Coord, Coord]


def call_with_args(func: Callable[..., Any], *args: Any) -> Any:
    """Call ``func`` with as many of the leading ``args`` as it requires and
    return its result. A parameter with a default does not count as required
    (so ``def f(_v=v)`` is called with none), matching the convention used
    elsewhere; a ``*args`` parameter receives everything."""
    import inspect

    try:
        parameters = inspect.signature(func).parameters.values()
    except (TypeError, ValueError):
        return func(*args)
    required = 0
    for p in parameters:
        if p.kind is p.VAR_POSITIONAL:
            return func(*args)
        if p.default is p.empty and p.kind in (
            p.POSITIONAL_ONLY,
            p.POSITIONAL_OR_KEYWORD,
        ):
            required += 1
    return func(*args[:required])


class Project:
    """Allocates relative paths and writes the files of an htsw project."""

    root: Path
    used_paths: set[str]
    item_paths: dict[str, str]

    def __init__(self, root: Path) -> None:
        self.root = root
        self.used_paths = set()
        self.item_paths = {}

    def _unique(self, base: str, ext: str) -> str:
        candidate = f'{base}{ext}'
        n = 2
        while candidate in self.used_paths:
            candidate = f'{base}-{n}{ext}'
            n += 1
        self.used_paths.add(candidate)
        return candidate

    def write(self, relpath: str, content: str) -> None:
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def write_block(self, base: str, block: 'Block') -> str:
        relpath = self._unique(base, '.htsl')
        self.write(relpath, f'{HEADER}\n{block.into_htsl()}\n')
        return relpath

    def item_path(self, item: 'Item | type[Item]', *, name: str | None = None) -> str:
        from .actions.item import normalize_item

        resolved = normalize_item(item)
        snbt = resolved.into_snbt()
        if name is None and snbt in self.item_paths:
            return self.item_paths[snbt]
        if name is not None:
            base = f'items/{into_kebab(name)}'
        else:
            suffix = hashlib.md5(snbt.encode()).hexdigest()[:8]
            base = f'items/{into_kebab(resolved.key)}-{suffix}'
        relpath = self._unique(base, '.snbt')
        self.write(relpath, snbt + '\n')
        self.item_paths[snbt] = relpath
        return relpath

    def icon(self, item: 'Item | type[Item]') -> dict[str, Any]:
        from .actions.item import normalize_item

        resolved = normalize_item(item)
        mid = resolved.minecraft_id()
        if ':' not in mid:
            mid = f'minecraft:{mid}'
        data: dict[str, Any] = {'item': mid}
        if resolved.count != 1:
            data['count'] = resolved.count
        if resolved.enchantments:
            data['enchanted'] = True
        return data


class Importable(ABC):
    kind: ClassVar[str]

    @abstractmethod
    def identifier(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def build(self, project: Project) -> dict[str, Any]:
        raise NotImplementedError


class FunctionImportable(Importable):
    kind = 'functions'

    def __init__(
        self,
        block: 'Block',
        *,
        name: str,
        repeat_ticks: int | None = None,
        icon: 'Item | type[Item] | None' = None,
    ) -> None:
        self.block = block
        self.name = name
        self.repeat_ticks = repeat_ticks
        self.icon = icon

    def identifier(self) -> str:
        return self.name

    def build(self, project: Project) -> dict[str, Any]:
        entry: dict[str, Any] = {'name': self.name}
        if not self.block.is_empty():
            entry['actions'] = project.write_block(
                f'functions/{into_kebab(self.name)}',
                self.block,
            )
        if self.repeat_ticks is not None:
            entry['repeatTicks'] = self.repeat_ticks
        if self.icon is not None:
            entry['icon'] = project.icon(self.icon)
        return entry


class EventImportable(Importable):
    kind = 'events'

    def __init__(self, block: 'Block', *, event: str) -> None:
        self.block = block
        self.event = event

    def identifier(self) -> str:
        return self.event

    def build(self, project: Project) -> dict[str, Any]:
        return {
            'event': self.event,
            'actions': project.write_block(
                f'events/{into_kebab(self.event)}',
                self.block,
            ),
        }


class ItemImportable(Importable):
    kind = 'items'

    def __init__(
        self,
        *,
        name: str,
        item: 'Item',
        left: 'Block | None' = None,
        right: 'Block | None' = None,
    ) -> None:
        self.name = name
        self.item = item
        self.left = left
        self.right = right

    def identifier(self) -> str:
        return self.name

    def build(self, project: Project) -> dict[str, Any]:
        entry: dict[str, Any] = {
            'name': self.name,
            'nbt': project.item_path(self.item, name=self.name),
        }
        folder = f'items/{into_kebab(self.name)}'
        if self.left is not None and not self.left.is_empty():
            entry['leftClickActions'] = project.write_block(f'{folder}/left', self.left)
        if self.right is not None and not self.right.is_empty():
            entry['rightClickActions'] = project.write_block(
                f'{folder}/right',
                self.right,
            )
        return entry


class RegionImportable(Importable):
    kind = 'regions'

    def __init__(
        self,
        *,
        name: str,
        bounds: Bounds | None = None,
        on_enter: 'Block | None' = None,
        on_exit: 'Block | None' = None,
    ) -> None:
        self.name = name
        self.bounds = bounds
        self.on_enter = on_enter
        self.on_exit = on_exit

    def identifier(self) -> str:
        return self.name

    def build(self, project: Project) -> dict[str, Any]:
        entry: dict[str, Any] = {'name': self.name}
        if self.bounds is not None:
            (fx, fy, fz), (tx, ty, tz) = self.bounds
            entry['bounds'] = {
                'from': {'x': fx, 'y': fy, 'z': fz},
                'to': {'x': tx, 'y': ty, 'z': tz},
            }
        folder = f'regions/{into_kebab(self.name)}'
        if self.on_enter is not None and not self.on_enter.is_empty():
            entry['onEnterActions'] = project.write_block(
                f'{folder}/enter',
                self.on_enter,
            )
        if self.on_exit is not None and not self.on_exit.is_empty():
            entry['onExitActions'] = project.write_block(f'{folder}/exit', self.on_exit)
        return entry


MenuAxis = int | Sequence[int] | None
# Receives (x, y), optionally also the Menu subclass; returns whether to fill.
XYCheck = Callable[[int, int], bool] | Callable[[int, int, 'type[Menu]'], bool]


class MenuSlot:
    def __init__(
        self,
        *,
        item: 'Item | type[Item]',
        x: MenuAxis,
        y: MenuAxis,
        xy_check: XYCheck | None,
        block: 'Block | None',
    ) -> None:
        self.item = item
        self.x = x
        self.y = y
        self.xy_check = xy_check
        self.block = block

    @property
    def specific(self) -> bool:
        return (
            isinstance(self.x, int)
            and isinstance(self.y, int)
            and self.xy_check is None
        )


def _norm(index: int, length: int, *, what: str, menu: str) -> int:
    resolved = index + length if index < 0 else index
    if not 0 <= resolved < length:
        raise ValueError(
            f'Menu "{menu}": {what} index {index} is out of range for size {length}.',
        )
    return resolved


def _resolve_axis(value: MenuAxis, length: int, *, what: str, menu: str) -> list[int]:
    if value is None:
        return list(range(length))
    if isinstance(value, int):
        return [_norm(value, length, what=what, menu=menu)]
    return [_norm(index, length, what=what, menu=menu) for index in value]


class MenuImportable(Importable):
    kind = 'menus'
    COLS = 9

    def __init__(
        self,
        *,
        name: str,
        size: int,
        slots: list[MenuSlot],
        menu_cls: 'type[Menu] | None' = None,
    ) -> None:
        self.name = name
        self.size = size
        self.slots = slots
        self.menu_cls = menu_cls

    def identifier(self) -> str:
        return self.name

    def _resolve(self) -> dict[int, MenuSlot]:
        rows = self.size
        grid: dict[int, MenuSlot] = {}
        specific: set[int] = set()
        for element in self.slots:
            xs = _resolve_axis(element.x, rows, what='x', menu=self.name)
            ys = _resolve_axis(element.y, self.COLS, what='y', menu=self.name)
            for r in xs:
                for c in ys:
                    if element.xy_check is not None and not call_with_args(
                        element.xy_check,
                        r,
                        c,
                        self.menu_cls,
                    ):
                        continue
                    slot = r * self.COLS + c
                    if slot in specific:
                        log(
                            f'\x1b[38;2;255;191;0mMenu "{self.name}": slot {slot} set with explicit x and y is being overridden.\x1b[0m',
                        )
                    grid[slot] = element
                    if element.specific:
                        specific.add(slot)
                    else:
                        specific.discard(slot)
        return grid

    def build(self, project: Project) -> dict[str, Any]:
        folder = f'menus/{into_kebab(self.name)}'
        grid = self._resolve()
        slots: list[dict[str, Any]] = []
        for slot in sorted(grid):
            element = grid[slot]
            entry: dict[str, Any] = {
                'slot': slot,
                'nbt': project.item_path(element.item),
            }
            if element.block is not None and not element.block.is_empty():
                entry['actions'] = project.write_block(
                    f'{folder}/slot-{slot // self.COLS}-{slot % self.COLS}',
                    element.block,
                )
            slots.append(entry)
        return {'name': self.name, 'size': self.size, 'slots': slots}


class NpcEquipment:
    SLOTS = ('helmet', 'chestplate', 'leggings', 'boots', 'hand')

    def __init__(
        self,
        *,
        helmet: 'Item | type[Item] | None' = None,
        chestplate: 'Item | type[Item] | None' = None,
        leggings: 'Item | type[Item] | None' = None,
        boots: 'Item | type[Item] | None' = None,
        hand: 'Item | type[Item] | None' = None,
    ) -> None:
        self.helmet = helmet
        self.chestplate = chestplate
        self.leggings = leggings
        self.boots = boots
        self.hand = hand

    def build(self, project: Project) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for slot in self.SLOTS:
            item = getattr(self, slot)
            if item is not None:
                out[slot] = project.item_path(item)
        return out


class NpcImportable(Importable):
    kind = 'npcs'

    def __init__(
        self,
        *,
        name: str,
        pos: Coord,
        left: 'Block | None' = None,
        right: 'Block | None' = None,
        look_at_players: bool | None = None,
        hide_name_tag: bool | None = None,
        skin: str | None = None,
        equipment: NpcEquipment | None = None,
    ) -> None:
        self.name = name
        self.pos = pos
        self.left = left
        self.right = right
        self.look_at_players = look_at_players
        self.hide_name_tag = hide_name_tag
        self.skin = skin
        self.equipment = equipment

    def identifier(self) -> str:
        return self.name

    def build(self, project: Project) -> dict[str, Any]:
        x, y, z = self.pos
        entry: dict[str, Any] = {'name': self.name, 'pos': {'x': x, 'y': y, 'z': z}}
        folder = f'npcs/{into_kebab(self.name)}'
        if self.left is not None and not self.left.is_empty():
            entry['leftClickActions'] = project.write_block(f'{folder}/left', self.left)
        if self.right is not None and not self.right.is_empty():
            entry['rightClickActions'] = project.write_block(
                f'{folder}/right',
                self.right,
            )
        if self.look_at_players is not None:
            entry['lookAtPlayers'] = self.look_at_players
        if self.hide_name_tag is not None:
            entry['hideNameTag'] = self.hide_name_tag
        if self.skin is not None:
            entry['skin'] = self.skin
        if self.equipment is not None:
            equipment = self.equipment.build(project)
            if equipment:
                entry['equipment'] = equipment
        return entry


SECTION_ORDER = ('items', 'menus', 'npcs', 'regions', 'functions', 'events')


def build_import_json(
    project: Project,
    importables: list[Importable],
) -> dict[str, Any]:
    entries: dict[str, list[dict[str, Any]]] = {kind: [] for kind in SECTION_ORDER}
    for kind in SECTION_ORDER:
        for importable in importables:
            if importable.kind == kind:
                entries[kind].append(importable.build(project))

    data: dict[str, Any] = {}
    for kind in ('functions', 'events', 'items', 'regions', 'menus', 'npcs'):
        if entries[kind]:
            data[kind] = entries[kind]
    return data


def export_import_json(project: Project, importables: list[Importable]) -> None:
    data = build_import_json(project, importables)
    project.write('import.json', json.dumps(data, indent=2) + '\n')
