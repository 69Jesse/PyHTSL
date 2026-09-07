import difflib
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict, cast, get_args

from pyhtsw.clone import MISSING, Missing
from pyhtsw.config import HERE
from pyhtsw.declarations.item_keys import (
    ENCHANTMENT_TO_ID,
    ColorType,
    HousingMenuTier,
    ItemKey,
    ItemKeyName,
    LeatherArmorKey,
    PlayerSkullItemKey,
)
from pyhtsw.generated.enums import UNSPAWNABLE_ITEMS, EnchantmentName
from pyhtsw.nbt import NBT, NBTByte, NBTCompound, NBTInt, NBTList, NBTShort, NBTString
from pyhtsw.utils.bounds import check_bounds
from pyhtsw.utils.caller import caller_module
from pyhtsw.utils.formatting import normalize_formatting, remove_formatting
from pyhtsw.utils.kebab import into_kebab
from pyhtsw.utils.warn import warn

__all__ = (
    'Enchantment',
    'normalize_item_key',
    'normalize_item',
    'Item',
)


class Enchantment:
    name: EnchantmentName
    level: int

    def __init__(
        self,
        name: EnchantmentName,
        level: int = 1,
    ) -> None:
        self.name = name
        self.level = level

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Enchantment):
            return NotImplemented
        return self.name == other.name and self.level == other.level

    def __hash__(self) -> int:
        return hash((self.name, self.level))


if TYPE_CHECKING:
    from pyhtsw.compiler.block import NamedBlock
    from pyhtsw.compiler.importable import ItemImportable


class ItemJsonData(TypedDict):
    key: str
    title: str
    name: str
    id: int
    data_value: int
    can_be_damaged: bool


ITEMS_JSON_FILE = HERE / 'misc' / 'items.json'
with ITEMS_JSON_FILE.open('r', encoding='utf-8') as file:
    ITEMS: dict[str, ItemJsonData] = json.load(file)


DAMAGEABLE_KEY_BY_NAME: dict[str, str] = {}
KEY_BY_NAME_AND_DATA: dict[tuple[str, int], str] = {}
for _key, _data in ITEMS.items():
    if _data['can_be_damaged']:
        DAMAGEABLE_KEY_BY_NAME[_data['name']] = _key
    else:
        KEY_BY_NAME_AND_DATA[(_data['name'], _data['data_value'])] = _key

ENCHANTMENT_BY_ID: dict[int, EnchantmentName] = {
    v: k for k, v in ENCHANTMENT_TO_ID.items()
}


HIDE_FLAGS: dict[str, int] = {
    'hide_enchantments_flag': 1,
    'hide_modifiers_flag': 2,
    'hide_unbreakable_flag': 4,
    'hide_additional_flag': 32,
    'hide_dye_flag': 64,
}
HIDE_FLAGS['hide_all_flags'] = max(HIDE_FLAGS.values()) * 2 - 1


_FIELD_DEFAULTS: dict[str, Any] = {
    'name': None,
    'lore': None,
    'count': 1,
    'enchantments': None,
    'unbreakable': False,
    'damage': 0,
    'color': None,
    'skull_data': None,
    'is_cookie_item': False,
    'housing_menu_tier': None,
    'hide_flags': None,
    'hide_all_flags': False,
    'hide_enchantments_flag': False,
    'hide_modifiers_flag': False,
    'hide_unbreakable_flag': False,
    'hide_additional_flag': False,
    'hide_dye_flag': False,
}


def normalize_item_key(key: ItemKey) -> str:
    if isinstance(key, str):
        return key
    return key[0]


# A click handler takes no args, or one arg that receives the Item instance.
ItemHandler = Callable[[], Any] | Callable[['Item'], Any]


def _resolve_click_handlers(
    on_click: 'ItemHandler | None',
    on_left_click: 'ItemHandler | None',
    on_right_click: 'ItemHandler | None',
) -> tuple['ItemHandler | None', 'ItemHandler | None']:
    if on_click is not None and (
        on_left_click is not None or on_right_click is not None
    ):
        warn(
            'Item given both "on_click" and an explicit '
            '"on_left_click"/"on_right_click"; the explicit side overrides '
            '"on_click".',
        )
    left = on_left_click if on_left_click is not None else on_click
    right = on_right_click if on_right_click is not None else on_click
    return left, right


class Item:
    __htsw_module__: 'str | None'
    # The items[] entry this item declares, when it has one: an interactive
    # item, or one `declare()` was called on. A plain item has none until the
    # export-time plan promotes it.
    __htsw_importable__: 'ItemImportable | None'
    # Filled in by the export-time item plan (see pyhtsw/item_plan.py): the htsw
    # name this instance is referenced by, and the module its .snbt is written
    # under once identical items across modules have been folded together.
    _reference_name: str | None
    _owner_module: str | None
    # `Item(..., importable=False)` keeps an item out of import.json.
    _promotable: bool

    key: ItemKeyName
    name: str | None
    lore: str | None
    count: int
    enchantments: list[Enchantment] | None
    unbreakable: bool
    damage: int
    color: ColorType
    skull_data: NBTCompound | None
    is_cookie_item: bool
    housing_menu_tier: 'HousingMenuTier | None'
    hide_flags: int | None
    hide_all_flags: bool
    hide_enchantments_flag: bool
    hide_modifiers_flag: bool
    hide_unbreakable_flag: bool
    hide_additional_flag: bool
    hide_dye_flag: bool

    def __init__(
        self,
        key: ItemKey | Missing = MISSING,
        *,
        name: str | None | Missing = MISSING,
        lore: str | None | Missing = MISSING,
        count: int | Missing = MISSING,
        enchantments: list[Enchantment] | None | Missing = MISSING,
        unbreakable: bool | Missing = MISSING,
        damage: int | Missing = MISSING,
        color: ColorType | Missing = MISSING,
        skull_data: NBTCompound | None | Missing = MISSING,
        is_cookie_item: bool | Missing = MISSING,
        housing_menu_tier: 'HousingMenuTier | None | Missing' = MISSING,
        hide_flags: int | None | Missing = MISSING,
        hide_all_flags: bool | Missing = MISSING,
        hide_enchantments_flag: bool | Missing = MISSING,
        hide_modifiers_flag: bool | Missing = MISSING,
        hide_unbreakable_flag: bool | Missing = MISSING,
        hide_additional_flag: bool | Missing = MISSING,
        hide_dye_flag: bool | Missing = MISSING,
        on_click: 'ItemHandler | None' = None,
        on_left_click: 'ItemHandler | None' = None,
        on_right_click: 'ItemHandler | None' = None,
        importable: bool = True,
    ) -> None:
        self.__htsw_module__ = caller_module()
        self.__htsw_importable__ = None
        self._reference_name = None
        self._owner_module = None
        self._promotable = importable
        explicit: dict[str, Any] = {
            'name': name,
            'lore': lore,
            'count': count,
            'enchantments': enchantments,
            'unbreakable': unbreakable,
            'damage': damage,
            'color': color,
            'skull_data': skull_data,
            'is_cookie_item': is_cookie_item,
            'housing_menu_tier': housing_menu_tier,
            'hide_flags': hide_flags,
            'hide_all_flags': hide_all_flags,
            'hide_enchantments_flag': hide_enchantments_flag,
            'hide_modifiers_flag': hide_modifiers_flag,
            'hide_unbreakable_flag': hide_unbreakable_flag,
            'hide_additional_flag': hide_additional_flag,
            'hide_dye_flag': hide_dye_flag,
        }

        if key is MISSING:
            raise TypeError('Item requires a "key".')
        resolved_key: Any = key

        faulty_tuple_key: str | None = None
        color_value: Any = explicit['color']
        skull_value: Any = explicit['skull_data']
        if isinstance(resolved_key, tuple):
            string_key, packed = resolved_key
            if string_key in get_args(LeatherArmorKey):
                color_value = packed
            elif string_key in get_args(PlayerSkullItemKey):
                skull_value = packed
            else:
                faulty_tuple_key = string_key
            resolved_key = string_key
        explicit['color'] = color_value
        explicit['skull_data'] = skull_value

        self.key = cast(ItemKeyName, resolved_key)
        for field, hard_default in _FIELD_DEFAULTS.items():
            value = explicit[field]
            setattr(self, field, hard_default if value is MISSING else value)

        self._get_item_data()
        self._check_spawnable()
        check_bounds(self.count, field='Item count', minimum=0, maximum=64)
        if faulty_tuple_key is not None:
            raise ValueError(
                f'Item key {faulty_tuple_key!r} does not take a tuple value',
            )

        left_fn, right_fn = _resolve_click_handlers(
            on_click,
            on_left_click,
            on_right_click,
        )
        self._left_click_handler = left_fn
        self._right_click_handler = right_fn
        self._importable_name: str | None = None
        if left_fn is not None or right_fn is not None:
            self.declare()

    def declare(self, name: str | None = None) -> 'Item':
        """Give this item its own items[] entry, so htsw writes its .snbt and
        the project tree shows it. Without a `name` it takes `derived_name()`.
        Returns the item, so `Item(...).declare()` reads as one expression."""
        existing = self.__htsw_importable__
        if existing is not None:
            if name is None or name == existing.name:
                return self
            if existing.item is self:
                self._rename_importable(existing, name)
                return self
            # This item only borrowed a twin's entry; asking for a name is
            # asking for one of its own, so register rather than rename theirs.
            self.__htsw_importable__ = None
        left_fn = self._left_click_handler
        right_fn = self._right_click_handler
        if name is None:
            twin = _registered_twin(self, left_fn, right_fn)
            if twin is not None:
                # htsw identifies an item by its NBT, so the twin already is
                # this entry - point at it rather than registering a duplicate.
                self._importable_name = twin.name
                self.__htsw_importable__ = twin
                return self
            name = _free_item_name(self.derived_name(), self.count)
        self._importable_name = name
        self.__htsw_importable__ = _register_item_instance_importable(
            name,
            self,
            left_fn,
            right_fn,
            module=self.__htsw_module__,
        )
        return self

    def _rename_importable(self, importable: 'ItemImportable', name: str) -> None:
        from pyhtsw.compiler.container import get_current_container

        get_current_container().rename_importable(importable, name)
        self._importable_name = name
        for side in ('left', 'right'):
            block = getattr(importable, side)
            if block is not None:
                block._name = f'{name} {side}'

    @property
    def importable(self) -> 'ItemImportable':
        """The items[] entry this item declares. Raises when it has none."""
        if self.__htsw_importable__ is None:
            raise RuntimeError(
                f'Item "{self.derived_name()}" declares no items[] entry, so '
                f'it has no importable to read. Call "declare()" or give it a '
                f'click handler.',
            )
        return self.__htsw_importable__

    def _attach(self, which: str, func: 'ItemHandler') -> None:
        sides = ('left', 'right') if which == 'both' else (which,)
        for side in sides:
            if getattr(self, f'_{side}_click_handler') is not None:
                raise RuntimeError(
                    f'Item "{self.derived_name()}" already has a {side}-click '
                    f'handler; a second one would never run.',
                )
            setattr(self, f'_{side}_click_handler', func)
        importable = self.__htsw_importable__
        if importable is None:
            self.declare()
            return
        # Already an items[] entry (a named item, or a twin it shares with) - it
        # just gains the action list. htsw identifies an item by its NBT, so a
        # twin is the same item and correctly gains it too.
        for side in sides:
            setattr(
                importable,
                side,
                _item_handler_block(importable.name, side, self, func),
            )

    def on_left_click(self, func: 'ItemHandler') -> 'ItemHandler':
        """`@item.on_left_click` - run these actions on a left click."""
        self._attach('left', func)
        return func

    def on_right_click(self, func: 'ItemHandler') -> 'ItemHandler':
        """`@item.on_right_click` - run these actions on a right click."""
        self._attach('right', func)
        return func

    def on_click(self, func: 'ItemHandler') -> 'ItemHandler':
        """`@item.on_click` - run these actions on either button."""
        self._attach('both', func)
        return func

    # Where the item came from and what export decided to call it, neither of
    # which is part of the item. `_snbt_cache` is lazy, so comparing it would
    # make an item stop equalling its twin the moment one of them rendered.
    _EQ_IGNORE: ClassVar[frozenset[str]] = frozenset(
        {
            '__htsw_module__',
            '__htsw_importable__',
            '_snbt_cache',
            '_reference_name',
            '_owner_module',
            '_left_click_handler',
            '_right_click_handler',
        },
    )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Item):
            return False
        ignore = self._EQ_IGNORE
        return {k: v for k, v in vars(self).items() if k not in ignore} == {
            k: v for k, v in vars(other).items() if k not in ignore
        }

    _HOUSING_MENU_ITEMS: ClassVar[dict[str, tuple[str, str]]] = {
        'GUEST': ('dark_oak_door', '&aHousing Menu&7 (Right Click)'),
        'TRUSTED_BUILDER': ('ghast_tear', '&aHousing Menu&7 (Right Click)'),
        'OWNER': ('nether_star', '&dHousing Menu&7 (Right Click)'),
    }

    @classmethod
    def housing_menu(cls, tier: HousingMenuTier = 'OWNER') -> 'Item':
        """Hypixel's Housing Menu item. Handing one out is how a player gets
        the menu without the permission that normally grants it."""
        key, name = cls._HOUSING_MENU_ITEMS[tier]
        return Item(
            cast(ItemKey, key),
            name=name,
            housing_menu_tier=tier,
            hide_flags=255,
        )

    @classmethod
    def from_path(cls, path: Path | str) -> 'Item':
        path = Path(path)
        if path.suffix != '.snbt':
            raise ValueError(
                f'Items can only be loaded from .snbt files, got {path.suffix!r}',
            )
        return cls.from_snbt(path.read_text(encoding='utf-8'))

    @classmethod
    def from_snbt(cls, snbt: str) -> 'Item':
        return cls.from_nbt(NBT.from_snbt(snbt.strip()))

    @classmethod
    def from_nbt(cls, nbt: NBT) -> 'Item':
        if not isinstance(nbt, NBTCompound):
            raise ValueError(f'Expected an NBT compound, got {type(nbt).__name__}')

        name = nbt['id'].value
        damage = nbt.get('Damage')
        damage_value = damage.value if damage is not None else 0

        options: dict[str, Any] = {}
        if name in DAMAGEABLE_KEY_BY_NAME:
            key = DAMAGEABLE_KEY_BY_NAME[name]
            if damage_value:
                options['damage'] = damage_value
        else:
            key = KEY_BY_NAME_AND_DATA.get((name, damage_value))
            if key is None:
                raise ValueError(
                    f'Could not resolve an item key from id {name!r} with data value {damage_value}.',
                )

        count = nbt.get('Count')
        if count is not None and count.value != 1:
            options['count'] = count.value

        tags = nbt.get('tag')
        if isinstance(tags, NBTCompound):
            cls._extract_tags(tags, options)

        return Item(cast(ItemKey, key), **options)

    @staticmethod
    def _extract_tags(tags: NBTCompound, options: dict[str, Any]) -> None:
        ench = tags.get('ench')
        if isinstance(ench, NBTList):
            options['enchantments'] = [
                Enchantment(ENCHANTMENT_BY_ID[entry['id'].value], entry['lvl'].value)
                for entry in ench.value
            ]

        if tags.get('Unbreakable') is not None:
            options['unbreakable'] = True

        hide_flags = tags.get('HideFlags')
        if hide_flags is not None:
            value = hide_flags.value
            if value == HIDE_FLAGS['hide_all_flags']:
                options['hide_all_flags'] = True
            elif value & ~HIDE_FLAGS['hide_all_flags']:
                options['hide_flags'] = value
            else:
                for flag, bit in HIDE_FLAGS.items():
                    if flag != 'hide_all_flags' and value & bit:
                        options[flag] = True

        display = tags.get('display')
        if isinstance(display, NBTCompound):
            lore = display.get('Lore')
            if isinstance(lore, NBTList):
                options['lore'] = '\n'.join(line.value for line in lore.value)
            display_name = display.get('Name')
            if display_name is not None:
                options['name'] = display_name.value
            color = display.get('color')
            if color is not None:
                options['color'] = color.value

        skull_owner = tags.get('SkullOwner')
        if skull_owner is not None:
            options['skull_data'] = skull_owner

        extra_attributes = tags.get('ExtraAttributes')
        if isinstance(extra_attributes, NBTCompound):
            if extra_attributes.get('COOKIE_ITEM') is not None:
                options['is_cookie_item'] = True
            tier = extra_attributes.get('HOUSING_MENU')
            if tier is not None:
                options['housing_menu_tier'] = str(tier.value)

    def get_item_name(self) -> str:
        return self._get_item_data()['title']

    def minecraft_id(self) -> str:
        return self._get_item_data()['name']

    def into_snbt(self, indent: int | None = 4) -> str:
        # An item's fields are fixed after construction (`cloned` makes a fresh
        # one), so the default render is memoised — finalize references the same
        # item many times (e.g. for its `.snbt` path hash).
        if indent != 4:
            return self.into_nbt().into_snbt(indent=indent)
        cached = self.__dict__.get('_snbt_cache')
        if cached is None:
            cached = self.into_nbt().into_snbt(indent=4)
            self.__dict__['_snbt_cache'] = cached
        return cached

    def into_nbt(self, data: ItemJsonData | None = None) -> NBTCompound[NBT]:
        if data is None:
            data = self._get_item_data()

        result: NBTCompound[NBT] = NBTCompound(
            {
                'id': NBTString(data['name']),
                'Count': NBTByte(self.count),
                'Damage': NBTShort(data['data_value']),
            },
        )

        tags = NBTCompound()

        if data['can_be_damaged']:
            result.put('Damage', NBTShort(self.damage))

        if self.enchantments is not None:
            tags.put(
                'ench',
                NBTList(
                    [
                        NBTCompound()
                        .put('lvl', NBTShort(enchantment.level))
                        .put('id', NBTShort(ENCHANTMENT_TO_ID[enchantment.name]))
                        for enchantment in self.enchantments
                    ],
                ),
            )

        if self.unbreakable:
            tags.put('Unbreakable', NBTByte(1))

        flags: int = (
            self.hide_flags
            if self.hide_flags is not None
            else min(
                sum(value for flag, value in HIDE_FLAGS.items() if getattr(self, flag)),
                HIDE_FLAGS['hide_all_flags'],
            )
        )
        if flags:
            tags.put('HideFlags', NBTInt(flags))

        display = NBTCompound()

        if self.lore is not None:
            lore = normalize_formatting(self.lore)
            display.put('Lore', NBTList([NBTString(line) for line in lore.split('\n')]))

        if self.name is not None:
            name = normalize_formatting(self.name)
            display.put('Name', NBTString(name))

        color: ColorType = self.color
        if color is not None:
            if not isinstance(color, int | str | tuple):
                raise ValueError(f'Invalid color type: {type(color)}')
            if isinstance(color, str):
                color = int(color.removeprefix('#'), 16)
            elif isinstance(color, tuple):
                color = color[0] << 16 | color[1] << 8 | color[2]
            display.put('color', NBTInt(color))

        if self.skull_data is not None:
            tags.put('SkullOwner', self.skull_data)

        if not display.is_empty():
            tags.put('display', display)

        extra_attributes = NBTCompound()

        if self.is_cookie_item:
            extra_attributes.put('COOKIE_ITEM', NBTByte(1))

        if self.housing_menu_tier is not None:
            extra_attributes.put(
                'HOUSING_MENU',
                NBTString(self.housing_menu_tier),
            )

        if not extra_attributes.is_empty():
            tags.put('ExtraAttributes', extra_attributes)

        if not tags.is_empty():
            result.put('tag', tags)

        return result

    def _check_spawnable(self) -> None:
        item_id = self._get_item_data()['name'].rpartition(':')[2]
        if item_id in UNSPAWNABLE_ITEMS:
            raise ValueError(
                f'Hypixel refuses to spawn {self.key!r} (minecraft:{item_id}), '
                f'so htsw cannot import it.',
            )

    def _get_item_data(self) -> ItemJsonData:
        item = ITEMS.get(self.key, None)
        if item is None:
            closest = difflib.get_close_matches(
                self.key.lower(),
                ITEMS.keys(),
                n=1,
                cutoff=0.0,
            )[0]
            raise ValueError(
                f'Invalid item key: \x1b[38;2;255;0;0m{self.key}\x1b[0m. Did you mean \x1b[38;2;0;255;0m{closest}\x1b[0m?',
            )
        return item

    def cloned(
        self,
        key: ItemKey | Missing = MISSING,
        *,
        name: str | None | Missing = MISSING,
        lore: str | None | Missing = MISSING,
        count: int | Missing = MISSING,
        enchantments: list[Enchantment] | None | Missing = MISSING,
        unbreakable: bool | Missing = MISSING,
        damage: int | Missing = MISSING,
        color: ColorType | Missing = MISSING,
        skull_data: NBTCompound | None | Missing = MISSING,
        is_cookie_item: bool | Missing = MISSING,
        housing_menu_tier: 'HousingMenuTier | None | Missing' = MISSING,
        hide_flags: int | None | Missing = MISSING,
        hide_all_flags: bool | Missing = MISSING,
        hide_enchantments_flag: bool | Missing = MISSING,
        hide_modifiers_flag: bool | Missing = MISSING,
        hide_unbreakable_flag: bool | Missing = MISSING,
        hide_additional_flag: bool | Missing = MISSING,
        hide_dye_flag: bool | Missing = MISSING,
        on_click: 'ItemHandler | None | Missing' = MISSING,
        on_left_click: 'ItemHandler | None | Missing' = MISSING,
        on_right_click: 'ItemHandler | None | Missing' = MISSING,
    ) -> 'Item':
        """Returns a copy of the item, overriding only the given values. The
        click handlers come along unless you replace them; pass `None` to make
        the copy inert."""
        overrides: dict[str, Any] = {
            'name': name,
            'lore': lore,
            'count': count,
            'enchantments': enchantments,
            'unbreakable': unbreakable,
            'damage': damage,
            'color': color,
            'skull_data': skull_data,
            'is_cookie_item': is_cookie_item,
            'housing_menu_tier': housing_menu_tier,
            'hide_flags': hide_flags,
            'hide_all_flags': hide_all_flags,
            'hide_enchantments_flag': hide_enchantments_flag,
            'hide_modifiers_flag': hide_modifiers_flag,
            'hide_unbreakable_flag': hide_unbreakable_flag,
            'hide_additional_flag': hide_additional_flag,
            'hide_dye_flag': hide_dye_flag,
        }
        resolved = {
            field: getattr(self, field) if value is MISSING else value
            for field, value in overrides.items()
        }
        if on_click is not MISSING:
            left = right = on_click
        else:
            left = self._left_click_handler
            right = self._right_click_handler
        if on_left_click is not MISSING:
            left = on_left_click
        if on_right_click is not MISSING:
            right = on_right_click
        return Item(
            self.key if key is MISSING else key,
            importable=self._promotable,
            on_left_click=left,
            on_right_click=right,
            **resolved,
        )

    def derived_name(self) -> str:
        """The htsw name this item wants, before uniquifying. Its display name
        wins; otherwise the vanilla title, with the stack size appended so the
        very common `Item(key, count=n)` variants do not all want one name."""
        if self.name is not None:
            derived = remove_formatting(self.name).strip()
            # htsw reads any reference ending in .snbt as a path, so a display
            # name that looks like one cannot be the htsw name.
            if derived and not derived.lower().endswith('.snbt'):
                return derived
        title = self.get_item_name()
        return f'{title} x{self.count}' if self.count > 1 else title

    def anonymous_path(self) -> str:
        """Relative .snbt path for this item, registering it with the active
        project so the file gets written on export."""
        from pyhtsw.compiler.container import get_current_container

        container = get_current_container()
        if container.project is not None:
            root_relpath = container.project.item_path(self)
            return container.project.item_reference(root_relpath)
        snbt = self.into_snbt()
        suffix = hashlib.md5(snbt.encode()).hexdigest()[:8]
        return f'items/{into_kebab(self.key)}-{suffix}.snbt'


def _registered_twin(
    item: 'Item',
    left_fn: 'ItemHandler | None',
    right_fn: 'ItemHandler | None',
) -> 'ItemImportable | None':
    from pyhtsw.compiler.container import get_current_container
    from pyhtsw.compiler.importable import ItemImportable

    snbt = item.into_snbt()
    for importable in get_current_container().importables:
        if not isinstance(importable, ItemImportable):
            continue
        if (importable.left is not None) != (left_fn is not None):
            continue
        if (importable.right is not None) != (right_fn is not None):
            continue
        if importable.item.into_snbt() == snbt:
            return importable
    return None


def _free_item_name(base: str, count: int) -> str:
    from pyhtsw.compiler.container import get_current_container

    taken = get_current_container().importables_by_key
    if ('items', base) not in taken:
        return base
    sized = base if count <= 1 or base.endswith(f' x{count}') else f'{base} x{count}'
    if ('items', sized) not in taken:
        return sized
    index = 2
    while ('items', f'{sized} {index}') in taken:
        index += 1
    return f'{sized} {index}'


def _item_handler_block(
    name: str,
    side: str,
    item: 'Item',
    handler: 'ItemHandler',
) -> 'NamedBlock':
    from pyhtsw.compiler.block import NamedBlock
    from pyhtsw.compiler.container import get_current_container
    from pyhtsw.compiler.importable import call_with_args

    block = NamedBlock(
        f'{name} {side}',
        callback=lambda: call_with_args(handler, item),
        importable_kind='items',
    )
    get_current_container().add_block(block)
    return block


def _register_item_instance_importable(
    name: str,
    item: 'Item',
    left_fn: 'ItemHandler | None',
    right_fn: 'ItemHandler | None',
    module: str | None = None,
) -> 'ItemImportable':
    from pyhtsw.compiler.container import get_current_container
    from pyhtsw.compiler.importable import ItemImportable

    importable = ItemImportable(
        name=name,
        item=item,
        left=(
            None
            if left_fn is None
            else _item_handler_block(name, 'left', item, left_fn)
        ),
        right=(
            None
            if right_fn is None
            else _item_handler_block(name, 'right', item, right_fn)
        ),
    )
    importable.module = module
    get_current_container().register_importable(importable)
    return importable


def normalize_item(value: Item) -> Item:
    if not isinstance(value, Item):
        raise TypeError(f'Expected an Item, got {value!r}')
    return value


def item_reference_name(value: Item) -> str | None:
    """The htsw items[] name `value` is referenced by, or None when it has none
    (a plain item in a container that was never planned, which falls back to a
    direct .snbt path)."""
    if not isinstance(value, Item):
        raise TypeError(f'Expected an Item, got {value!r}')
    return value._importable_name or value._reference_name


def item_action_reference(value: Item) -> str:
    """How an item is referenced from an action: by its htsw name when it has
    one (a declared item, or a plain one the item plan promoted), otherwise by
    its .snbt path."""
    name = item_reference_name(value)
    return name if name is not None else value.anonymous_path()


def item_referenced_importables(value: Item) -> list[tuple[str, str]]:
    """`referenced_importables()` entry for an item field. A name that no
    importable claims (an item named only so its .snbt file reads nicely) is
    dropped by the include resolver, which looks names up against the real
    importables."""
    name = item_reference_name(value)
    return [('items', name)] if name is not None else []
