import hashlib
import posixpath
import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pyhtsw.generated.enums import (
    CHAT_SPEED_TO_HTSW,
    COMMAND_MODE_TO_HTSW,
    EVENT_NAME_TO_HTSW,
    GAMEMODE_TO_DEFAULT_GAMEMODE,
    HOUSING_COLOR_TO_HTSW,
    NPC_SKIN_TO_HTSW,
    PERMISSION_TO_HTSW,
    ChatSpeed,
    CommandMode,
    EventName,
    Gamemode,
    HousingColor,
    NpcSkin,
    Permission,
)
from pyhtsw.utils.kebab import into_kebab
from pyhtsw.utils.warn import SourceSite, warn_at

_ILLEGAL_HTSL_CHARS = frozenset(chr(code) for code in range(0x20)) | {
    '\x7f',
    '§',
}


def _verify_chat_safe(relpath: str, content: str) -> None:
    for number, line in enumerate(content.split('\n'), start=1):
        for column, char in enumerate(line, start=1):
            if char not in _ILLEGAL_HTSL_CHARS:
                continue
            raise ValueError(
                f'{relpath}:{number}:{column} emits U+{ord(char):04X}, which '
                f"Minecraft's chat cannot carry, so Housing would disconnect "
                f'the importer with "Illegal characters in chat". '
                f'Line: {line!r}',
            )


def _reserved_folder_names() -> frozenset[str]:
    names: set[str] = set()
    stack = list(Importable.__subclasses__())
    while stack:
        cls = stack.pop()
        kind = getattr(cls, 'kind', None)
        if kind:
            names.add(kind)
        stack.extend(cls.__subclasses__())
    return frozenset(names)


def module_to_folder(dotted: str | None) -> str:
    """Root-relative folder for a Python module in the multi-folder export. The
    entry script (`None`/`__main__`) is the project root (''); every other
    module contributes one `<kebab>` segment per dotted component, e.g.
    `features.general.combat` -> `features/general/combat`. A segment that would
    collide with one of a node's own importable folders (`items`, `functions`,
    ...) gets a `-module` suffix, e.g. `items.abilities` -> `items-module/abilities`."""
    if not dotted or dotted == '__main__':
        return ''
    reserved = _reserved_folder_names()
    parts: list[str] = []
    for part in dotted.split('.'):
        folder = into_kebab(part)
        if folder in reserved:
            folder = f'{folder}-module'
        parts.append(folder)
    return '/'.join(parts)


if TYPE_CHECKING:
    from pyhtsw.compiler.block import Block
    from pyhtsw.compiler.item_plan import ItemPlan
    from pyhtsw.declarations.item import Item
    from pyhtsw.declarations.menu import Menu

__all__ = (
    'EVENTS',
    'EventName',
    'NpcSkin',
    'Coord',
    'Bounds',
)


HEADER = '// Generated with PyHTSW (https://github.com/69Jesse/pyhtsw)'

# A 0-arg handler (the importable has no runtime instance to hand back).
Handler = Callable[[], Any] | Callable[[Any], Any]

EVENTS: tuple[EventName, ...] = tuple(EVENT_NAME_TO_HTSW)


Coord = tuple[int, int, int]
Bounds = tuple[Coord, Coord]


def _block_pos(pos: Coord, *, what: str) -> dict[str, int]:
    for axis, value in zip('xyz', pos, strict=True):
        if not (isinstance(value, int) or float(value).is_integer()):
            raise ValueError(
                f'{what}: coordinate {axis}={value} must be a whole number.',
            )
    x, y, z = pos
    return {'x': int(x), 'y': int(y), 'z': int(z)}


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
    written_paths: set[Path]
    item_paths: dict[str, str]
    item_plan: 'ItemPlan | None'
    current_block_relpath: str | None
    node_folder: str
    module_folder: Callable[[str | None], str]

    def __init__(self, root: Path, item_plan: 'ItemPlan | None' = None) -> None:
        self.root = root
        self.used_paths = set()
        self.written_paths = set()
        self.item_paths = {}
        self.item_plan = item_plan
        self.current_block_relpath = None
        self.node_folder = ''
        self.module_folder = module_to_folder

    def relative_to_node(self, root_relpath: str) -> str:
        """A root-relative path rewritten relative to the current node's folder,
        for use in that node's import.json (htsw resolves entry paths relative to
        the import.json that declares them)."""
        if not self.node_folder:
            return root_relpath
        return posixpath.relpath(root_relpath, self.node_folder)

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
        if path.suffix.lower() == '.htsl':
            _verify_chat_safe(relpath, content)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        self.written_paths.add(path)

    OWNED_SUFFIXES: ClassVar[frozenset[str]] = frozenset({'.htsl', '.snbt'})

    def _is_owned(self, path: Path) -> bool:
        return path.suffix.lower() in self.OWNED_SUFFIXES or path.name == 'import.json'

    def cleanup_stale(self) -> None:
        """Delete owned files this export did not (re)write, then prune the empty
        directories that leaves. Non-owned files and their folders survive."""
        if not self.root.exists():
            return
        for path in self.root.rglob('*'):
            if (
                path.is_file()
                and self._is_owned(path)
                and path not in self.written_paths
            ):
                path.unlink()
        for path in sorted(
            self.root.rglob('*'),
            key=lambda p: len(p.parts),
            reverse=True,
        ):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()

    def _node_base(self, base: str) -> str:
        return posixpath.join(self.node_folder, base) if self.node_folder else base

    def write_block(self, base: str, block: 'Block') -> str:
        relpath = self._unique(self._node_base(base), '.htsl')
        self.current_block_relpath = relpath
        try:
            content = block.into_htsl()
        finally:
            self.current_block_relpath = None
        self.write(relpath, f'{HEADER}\n{content}\n')
        return self.relative_to_node(relpath)

    def item_reference(self, root_relpath: str) -> str:
        """A root-relative item path rewritten relative to the block currently
        being rendered (for direct .snbt references inside actions)."""
        if self.current_block_relpath is None:
            return root_relpath
        block_dir = posixpath.dirname(self.current_block_relpath)
        if not block_dir:
            return root_relpath
        return posixpath.relpath(root_relpath, block_dir)

    def item_path(self, item: 'Item') -> str:
        """Write `item`'s .snbt and return the root-relative path. One file per
        distinct item: the plan folded identical items across modules together
        and picked the name and owning module, so two menus showing the same
        item share a file instead of each writing their own copy."""
        from pyhtsw.declarations.item import normalize_item

        resolved = normalize_item(item)
        snbt = resolved.into_snbt()
        existing = self.item_paths.get(snbt)
        if existing is not None:
            return existing

        entry = self.item_plan.lookup(resolved) if self.item_plan is not None else None
        if entry is not None:
            owner = entry.owner_module
            base = f'items/{into_kebab(entry.name)}'
        else:
            # No plan (a bare `Project`, or an item built after finalize): keep
            # the content-addressed name so the file is at least stable.
            owner = (
                getattr(item, '__module__', None)
                if isinstance(item, type)
                else getattr(item, '__htsw_module__', None)
            )
            suffix = hashlib.md5(snbt.encode()).hexdigest()[:8]
            base = f'items/{into_kebab(resolved.key)}-{suffix}'
        owner_folder = self.module_folder(owner)
        relpath = self._unique(
            posixpath.join(owner_folder, base) if owner_folder else base,
            '.snbt',
        )
        self.write(relpath, snbt + '\n')
        self.item_paths[snbt] = relpath
        return relpath

    def icon(self, item: 'Item') -> dict[str, Any]:
        from pyhtsw.declarations.item import normalize_item

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


def _block_replayer(block: 'Block') -> Callable[[], None]:
    if block.callback is not None:
        return block.callback

    expressions = block.expressions

    def replay() -> None:
        for expr in expressions:
            expr.cloned().write()

    return replay


def _clone_block_into_current(block: 'Block | None') -> 'Block | None':
    if block is None:
        return None
    from pyhtsw.compiler.block import NamedBlock
    from pyhtsw.compiler.container import get_current_container

    fresh = NamedBlock(
        block.get_name(),
        callback=_block_replayer(block),
        importable_kind=block.importable_kind,
    )
    get_current_container().add_block(fresh)
    return fresh


class Importable(ABC):
    kind: ClassVar[str]
    module: str | None = None

    @abstractmethod
    def identifier(self) -> str:
        raise NotImplementedError

    def unique_key(self) -> tuple[str, str] | None:
        """A second field htsw rejects duplicates on, as (label, value).
        Only NPCs have one: htsw identifies them by position, not name."""
        return None

    def rename(self, name: str) -> None:
        """Change what `identifier()` returns. Go through
        `Container.rename_importable`, which keeps the name index in step."""
        self.name = name  # type: ignore[attr-defined]

    @abstractmethod
    def build(self, project: Project) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def reexport(self) -> None:
        """Re-register an equivalent importable into the current container,
        re-running this one's action callbacks there. Used by `pyhtsw.compiler.export`
        to gather importables from a module into a fresh project container."""
        raise NotImplementedError


class FunctionImportable(Importable):
    kind = 'functions'

    def __init__(
        self,
        block: 'Block',
        *,
        name: str,
        repeat_ticks: int | None = None,
        icon: 'Item | None' = None,
    ) -> None:
        if repeat_ticks is not None and not 4 <= repeat_ticks <= 18000:
            raise ValueError(
                f'Function "{name}": repeat_ticks {repeat_ticks} must be 4-18000.',
            )
        self.block = block
        self.name = name
        self.repeat_ticks = repeat_ticks
        self.icon = icon

    def identifier(self) -> str:
        return self.name

    def reexport(self) -> None:
        from pyhtsw.declarations.function import function

        value = function(
            name=self.name,
            repeat_ticks=self.repeat_ticks,
            icon=self.icon,
        )(_block_replayer(self.block))
        value.declaration().module = self.module

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
    event: EventName

    def __init__(self, block: 'Block', *, event: EventName) -> None:
        self.block = block
        self.event = event

    def identifier(self) -> str:
        return self.event

    def rename(self, name: str) -> None:
        self.event = cast('EventName', name)

    def reexport(self) -> None:
        from pyhtsw.declarations.event import event

        value = event(self.event)(_block_replayer(self.block))  # type: ignore[arg-type]
        value.declaration().module = self.module

    def build(self, project: Project) -> dict[str, Any]:
        return {
            'event': EVENT_NAME_TO_HTSW[self.event],
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

    def reexport(self) -> None:
        from pyhtsw.compiler.container import get_current_container

        get_current_container().register_importable(
            ItemImportable(
                name=self.name,
                item=self.item,
                left=_clone_block_into_current(self.left),
                right=_clone_block_into_current(self.right),
            ),
        )

    def build(self, project: Project) -> dict[str, Any]:
        entry: dict[str, Any] = {
            'name': self.name,
            'nbt': project.relative_to_node(project.item_path(self.item)),
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
        bounds: Bounds,
        on_enter: 'Block | None' = None,
        on_exit: 'Block | None' = None,
    ) -> None:
        self.name = name
        self.bounds = bounds
        self.on_enter = on_enter
        self.on_exit = on_exit

    def identifier(self) -> str:
        return self.name

    def reexport(self) -> None:
        from pyhtsw.compiler.container import get_current_container

        get_current_container().register_importable(
            RegionImportable(
                name=self.name,
                bounds=self.bounds,
                on_enter=_clone_block_into_current(self.on_enter),
                on_exit=_clone_block_into_current(self.on_exit),
            ),
        )

    def build(self, project: Project) -> dict[str, Any]:
        what = f'Region "{self.name}"'
        if self.bounds is None:
            raise ValueError(
                f'{what} has no bounds, which htsw requires. Pass '
                f'bounds=((x, y, z), (x, y, z)), or refer to a region built in-game '
                f'by its name string rather than declaring one.',
            )
        entry: dict[str, Any] = {
            'name': self.name,
            'bounds': {
                'from': _block_pos(self.bounds[0], what=what),
                'to': _block_pos(self.bounds[1], what=what),
            },
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
# Receives (x, y), optionally also the menu itself; returns whether to fill.
XYCheck = Callable[[int, int], bool] | Callable[[int, int, 'Menu'], bool]


class MenuSlot:
    def __init__(
        self,
        *,
        item: 'Item',
        x: MenuAxis,
        y: MenuAxis,
        xy_check: XYCheck | None,
        block: 'Block | None',
        site: SourceSite | None = None,
    ) -> None:
        self.item = item
        self.x = x
        self.y = y
        self.xy_check = xy_check
        self.block = block
        self.site = site

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
        menu: 'Menu | None' = None,
    ) -> None:
        self.name = name
        self.size = size
        self.slots = slots
        self.menu = menu

    def identifier(self) -> str:
        return self.name

    def reexport(self) -> None:
        from pyhtsw.compiler.container import get_current_container

        slots = [
            MenuSlot(
                item=slot.item,
                x=slot.x,
                y=slot.y,
                xy_check=slot.xy_check,
                block=_clone_block_into_current(slot.block),
                site=slot.site,
            )
            for slot in self.slots
        ]
        get_current_container().register_importable(
            MenuImportable(
                name=self.name,
                size=self.size,
                slots=slots,
                menu=self.menu,
            ),
        )

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
                        self.menu,
                    ):
                        continue
                    slot = r * self.COLS + c
                    if slot in specific:
                        warn_at(
                            f'Menu "{self.name}": slot {slot} set with explicit x and y is being overridden.',
                            element.site,
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
                'nbt': project.relative_to_node(project.item_path(element.item)),
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
        helmet: 'Item | None' = None,
        chestplate: 'Item | None' = None,
        leggings: 'Item | None' = None,
        boots: 'Item | None' = None,
        hand: 'Item | None' = None,
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
                out[slot] = project.relative_to_node(project.item_path(item))
        return out


class NpcImportable(Importable):
    kind = 'npcs'
    skin: NpcSkin | None

    def __init__(
        self,
        *,
        name: str,
        pos: Coord,
        left: 'Block | None' = None,
        right: 'Block | None' = None,
        left_click_redirect: bool | None = None,
        look_at_players: bool | None = None,
        hide_name_tag: bool | None = None,
        skin: NpcSkin | None = None,
        equipment: NpcEquipment | None = None,
    ) -> None:
        self.name = name
        self.pos = pos
        self.left = left
        self.right = right
        self.left_click_redirect = left_click_redirect
        self.look_at_players = look_at_players
        self.hide_name_tag = hide_name_tag
        self.skin = skin
        self.equipment = equipment

    def identifier(self) -> str:
        return self.name

    def unique_key(self) -> tuple[str, str] | None:
        x, y, z = self.pos
        return ('position', f'{x},{y},{z}')

    def reexport(self) -> None:
        from pyhtsw.compiler.container import get_current_container

        get_current_container().register_importable(
            NpcImportable(
                name=self.name,
                pos=self.pos,
                left=_clone_block_into_current(self.left),
                right=_clone_block_into_current(self.right),
                left_click_redirect=self.left_click_redirect,
                look_at_players=self.look_at_players,
                hide_name_tag=self.hide_name_tag,
                skin=self.skin,
                equipment=self.equipment,
            ),
        )

    def build(self, project: Project) -> dict[str, Any]:
        entry: dict[str, Any] = {
            'name': self.name,
            'pos': _block_pos(self.pos, what=f'NPC "{self.name}"'),
        }
        folder = f'npcs/{into_kebab(self.name)}'
        if self.left is not None and not self.left.is_empty():
            entry['leftClickActions'] = project.write_block(f'{folder}/left', self.left)
        if self.right is not None and not self.right.is_empty():
            entry['rightClickActions'] = project.write_block(
                f'{folder}/right',
                self.right,
            )
        if self.left_click_redirect is not None:
            entry['leftClickRedirect'] = self.left_click_redirect
        if self.look_at_players is not None:
            entry['lookAtPlayers'] = self.look_at_players
        if self.hide_name_tag is not None:
            entry['hideNameTag'] = self.hide_name_tag
        if self.skin is not None:
            entry['skin'] = NPC_SKIN_TO_HTSW[self.skin]
        if self.equipment is not None:
            equipment = self.equipment.build(project)
            if equipment:
                entry['equipment'] = equipment
        return entry


TAG_PATTERN = re.compile(r'^[A-Za-z0-9 -]*$')


def _check_tag(name: str, tag: str | None) -> None:
    if tag is not None and TAG_PATTERN.match(tag) is None:
        raise ValueError(
            f'"{name}": tag {tag!r} must contain only letters, digits, '
            'spaces and hyphens.',
        )


class TeamImportable(Importable):
    kind = 'teams'
    color: HousingColor | None

    def __init__(
        self,
        *,
        name: str,
        tag: str | None = None,
        color: HousingColor | None = None,
        friendly_fire: bool | None = None,
    ) -> None:
        _check_tag(name, tag)
        self.name = name
        self.tag = tag
        self.color = color
        self.friendly_fire = friendly_fire

    def identifier(self) -> str:
        return self.name

    def reexport(self) -> None:
        from pyhtsw.compiler.container import get_current_container

        get_current_container().register_importable(
            TeamImportable(
                name=self.name,
                tag=self.tag,
                color=self.color,
                friendly_fire=self.friendly_fire,
            ),
        )

    def build(self, project: Project) -> dict[str, Any]:
        entry: dict[str, Any] = {'name': self.name}
        if self.tag is not None:
            entry['tag'] = self.tag
        if self.color is not None:
            entry['color'] = HOUSING_COLOR_TO_HTSW[self.color]
        if self.friendly_fire is not None:
            entry['friendlyFire'] = self.friendly_fire
        return entry


class GroupImportable(Importable):
    kind = 'groups'
    color: HousingColor | None
    chat_speed: ChatSpeed | None
    default_gamemode: Gamemode | None

    def __init__(
        self,
        *,
        name: str,
        tag: str | None = None,
        tag_shown_in_chat: bool | None = None,
        color: HousingColor | None = None,
        priority: int | None = None,
        permissions: dict[Permission, bool] | None = None,
        chat_speed: ChatSpeed | None = None,
        default_gamemode: Gamemode | None = None,
    ) -> None:
        _check_tag(name, tag)
        if priority is not None and not 0 <= priority <= 20:
            raise ValueError(f'Group "{name}": priority {priority} must be 0-20.')
        self.name = name
        self.tag = tag
        self.tag_shown_in_chat = tag_shown_in_chat
        self.color = color
        self.priority = priority
        self.permissions = permissions
        self.chat_speed = chat_speed
        self.default_gamemode = default_gamemode

    def identifier(self) -> str:
        return self.name

    def reexport(self) -> None:
        from pyhtsw.compiler.container import get_current_container

        get_current_container().register_importable(
            GroupImportable(
                name=self.name,
                tag=self.tag,
                tag_shown_in_chat=self.tag_shown_in_chat,
                color=self.color,
                priority=self.priority,
                permissions=dict(self.permissions) if self.permissions else None,
                chat_speed=self.chat_speed,
                default_gamemode=self.default_gamemode,
            ),
        )

    def build(self, project: Project) -> dict[str, Any]:
        entry: dict[str, Any] = {'name': self.name}
        if self.tag is not None:
            entry['tag'] = self.tag
        if self.tag_shown_in_chat is not None:
            entry['tagShownInChat'] = self.tag_shown_in_chat
        if self.color is not None:
            entry['color'] = HOUSING_COLOR_TO_HTSW[self.color]
        if self.priority is not None:
            entry['priority'] = self.priority
        if self.permissions:
            entry['permissions'] = {
                PERMISSION_TO_HTSW[permission]: allowed
                for permission, allowed in self.permissions.items()
            }
        if self.chat_speed is not None:
            entry['chatSpeed'] = CHAT_SPEED_TO_HTSW[self.chat_speed]
        if self.default_gamemode is not None:
            entry['defaultGameMode'] = GAMEMODE_TO_DEFAULT_GAMEMODE[
                self.default_gamemode
            ]
        return entry


class CommandImportable(Importable):
    kind = 'commands'
    mode: CommandMode | None

    def __init__(
        self,
        block: 'Block',
        *,
        name: str,
        mode: CommandMode | None = None,
        required_priority: int | None = None,
        listed: bool | None = None,
    ) -> None:
        if required_priority is not None and not 0 <= required_priority <= 20:
            raise ValueError(
                f'Command "{name}": required_priority {required_priority} must be 0-20.',
            )
        self.block = block
        self.name = name
        self.mode = mode
        self.required_priority = required_priority
        self.listed = listed

    def identifier(self) -> str:
        return self.name

    def reexport(self) -> None:
        from pyhtsw.declarations.command import command

        value = command(
            name=self.name,
            mode=self.mode,
            required_priority=self.required_priority,
            listed=self.listed,
        )(_block_replayer(self.block))
        value.declaration().module = self.module

    def build(self, project: Project) -> dict[str, Any]:
        entry: dict[str, Any] = {'name': self.name}
        if not self.block.is_empty():
            entry['actions'] = project.write_block(
                f'commands/{into_kebab(self.name)}',
                self.block,
            )
        if self.mode is not None:
            entry['mode'] = COMMAND_MODE_TO_HTSW[self.mode]
        if self.required_priority is not None:
            entry['requiredPriority'] = self.required_priority
        if self.listed is not None:
            entry['listed'] = self.listed
        return entry


# Items first so a menu/npc referencing one resolves its .snbt path; the rest
# follows the order htsw's own schema lists them in.
SECTION_ORDER = (
    'items',
    'menus',
    'npcs',
    'regions',
    'functions',
    'events',
    'teams',
    'groups',
    'commands',
)

JSON_SECTION_ORDER = (
    'functions',
    'events',
    'regions',
    'items',
    'menus',
    'teams',
    'groups',
    'commands',
    'npcs',
)


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
    for kind in JSON_SECTION_ORDER:
        if entries[kind]:
            data[kind] = entries[kind]
    return data
