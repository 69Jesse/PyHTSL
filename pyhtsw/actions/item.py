import difflib
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, TypedDict, cast, get_args

from ..config import HERE
from ..nbt import NBT, NBTByte, NBTCompound, NBTInt, NBTList, NBTShort, NBTString
from ..types import (
    ALL_ENCHANTMENTS,
    ALL_ITEM_KEY_STRINGS,
    ALL_ITEM_KEYS,
    ENCHANTMENT_TO_ID,
    LEATHER_ARMOR_KEYS,
    PLAYER_SKULL_ITEM_KEY,
    ColorType,
)
from ..utils.formatting import normalize_formatting, remove_formatting
from ..utils.kebab import into_kebab
from .enchantment import Enchantment

__all__ = (
    'normalize_item_key',
    'normalize_item',
    'Item',
)


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

ENCHANTMENT_BY_ID: dict[int, ALL_ENCHANTMENTS] = {
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


class _MissingType:
    __slots__ = ()


MISSING = _MissingType()

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
    'hide_all_flags': False,
    'hide_enchantments_flag': False,
    'hide_modifiers_flag': False,
    'hide_unbreakable_flag': False,
    'hide_additional_flag': False,
    'hide_dye_flag': False,
}


def normalize_item_key(key: ALL_ITEM_KEYS) -> str:
    if isinstance(key, str):
        return key
    return key[0]


def left_click(func: Callable[[], None]) -> Callable[[], None]:
    func.__htsw_click__ = 'left'  # type: ignore[attr-defined]
    return func


def right_click(func: Callable[[], None]) -> Callable[[], None]:
    func.__htsw_click__ = 'right'  # type: ignore[attr-defined]
    return func


def click(func: Callable[[], None]) -> Callable[[], None]:
    func.__htsw_click__ = 'both'  # type: ignore[attr-defined]
    return func


# A click handler takes no args, or one arg that receives the Item instance.
ItemHandler = Callable[[], Any] | Callable[['Item'], Any]


def _resolve_click_handlers(
    on_click: 'ItemHandler | None',
    on_left_click: 'ItemHandler | None',
    on_right_click: 'ItemHandler | None',
) -> tuple['ItemHandler | None', 'ItemHandler | None']:
    """on_click applies to both buttons; an explicit side overrides it."""
    if on_click is not None and (
        on_left_click is not None or on_right_click is not None
    ):
        from ..utils.log import log

        log(
            '\x1b[38;2;255;191;0mItem given both "on_click" and an explicit '
            '"on_left_click"/"on_right_click"; the explicit side overrides '
            '"on_click".\x1b[0m',
        )
    left = on_left_click if on_left_click is not None else on_click
    right = on_right_click if on_right_click is not None else on_click
    return left, right


class Item:
    # Subclasses become items[] importables; the class name is the htsw reference.
    __htsw_name__: ClassVar[str | None] = None
    __htsw_item_defaults__: ClassVar[dict[str, Any]] = {}

    left_click = staticmethod(left_click)
    right_click = staticmethod(right_click)
    click = staticmethod(click)

    key: ALL_ITEM_KEY_STRINGS
    name: str | None
    lore: str | None
    count: int
    enchantments: list[Enchantment] | None
    unbreakable: bool
    damage: int
    color: ColorType
    skull_data: NBTCompound | None
    is_cookie_item: bool
    hide_all_flags: bool
    hide_enchantments_flag: bool
    hide_modifiers_flag: bool
    hide_unbreakable_flag: bool
    hide_additional_flag: bool
    hide_dye_flag: bool

    def __init__(
        self,
        key: ALL_ITEM_KEYS | _MissingType = MISSING,
        *,
        name: str | None | _MissingType = MISSING,
        lore: str | None | _MissingType = MISSING,
        count: int | _MissingType = MISSING,
        enchantments: list[Enchantment] | None | _MissingType = MISSING,
        unbreakable: bool | _MissingType = MISSING,
        damage: int | _MissingType = MISSING,
        color: ColorType | _MissingType = MISSING,
        skull_data: NBTCompound | None | _MissingType = MISSING,
        is_cookie_item: bool | _MissingType = MISSING,
        hide_all_flags: bool | _MissingType = MISSING,
        hide_enchantments_flag: bool | _MissingType = MISSING,
        hide_modifiers_flag: bool | _MissingType = MISSING,
        hide_unbreakable_flag: bool | _MissingType = MISSING,
        hide_additional_flag: bool | _MissingType = MISSING,
        hide_dye_flag: bool | _MissingType = MISSING,
        on_click: 'ItemHandler | None' = None,
        on_left_click: 'ItemHandler | None' = None,
        on_right_click: 'ItemHandler | None' = None,
        importable_name: str | None = None,
    ) -> None:
        defaults = type(self).__htsw_item_defaults__
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
            'hide_all_flags': hide_all_flags,
            'hide_enchantments_flag': hide_enchantments_flag,
            'hide_modifiers_flag': hide_modifiers_flag,
            'hide_unbreakable_flag': hide_unbreakable_flag,
            'hide_additional_flag': hide_additional_flag,
            'hide_dye_flag': hide_dye_flag,
        }

        resolved_key = (
            key if not isinstance(key, _MissingType) else defaults.get('key', MISSING)
        )
        if isinstance(resolved_key, _MissingType):
            raise TypeError('Item requires a "key".')

        faulty_tuple_key: str | None = None
        color_value: Any = explicit['color']
        skull_value: Any = explicit['skull_data']
        if isinstance(resolved_key, tuple):
            string_key, packed = resolved_key
            if string_key in get_args(LEATHER_ARMOR_KEYS):
                color_value = packed
            elif string_key in get_args(PLAYER_SKULL_ITEM_KEY):
                skull_value = packed
            else:
                faulty_tuple_key = string_key
            resolved_key = string_key
        explicit['color'] = color_value
        explicit['skull_data'] = skull_value

        self.key = cast(ALL_ITEM_KEY_STRINGS, resolved_key)
        for field, hard_default in _FIELD_DEFAULTS.items():
            value = explicit[field]
            if isinstance(value, _MissingType):
                value = defaults.get(field, hard_default)
            setattr(self, field, value)

        self._get_item_data()
        if faulty_tuple_key is not None:
            raise ValueError(
                f'Item key {faulty_tuple_key!r} does not take a tuple value',
            )

        left_fn, right_fn = _resolve_click_handlers(
            on_click,
            on_left_click,
            on_right_click,
        )
        self._importable_name: str | None = None
        if left_fn is not None or right_fn is not None or importable_name is not None:
            resolved_name = importable_name
            if resolved_name is None:
                if self.name is None:
                    raise TypeError(
                        'An interactive Item (with on_click/on_left_click/'
                        'on_right_click) needs a "name" or "importable_name".',
                    )
                resolved_name = remove_formatting(self.name).strip()
            self._importable_name = resolved_name
            _register_item_instance_importable(
                resolved_name,
                self,
                left_fn,
                right_fn,
            )

    def __init_subclass__(
        cls,
        key: ALL_ITEM_KEYS | _MissingType = MISSING,
        name: str | None | _MissingType = MISSING,
        lore: str | None | _MissingType = MISSING,
        count: int | _MissingType = MISSING,
        enchantments: list[Enchantment] | None | _MissingType = MISSING,
        unbreakable: bool | _MissingType = MISSING,
        damage: int | _MissingType = MISSING,
        color: ColorType | _MissingType = MISSING,
        skull_data: NBTCompound | None | _MissingType = MISSING,
        is_cookie_item: bool | _MissingType = MISSING,
        hide_all_flags: bool | _MissingType = MISSING,
        hide_enchantments_flag: bool | _MissingType = MISSING,
        hide_modifiers_flag: bool | _MissingType = MISSING,
        hide_unbreakable_flag: bool | _MissingType = MISSING,
        hide_additional_flag: bool | _MissingType = MISSING,
        hide_dye_flag: bool | _MissingType = MISSING,
        on_click: ItemHandler | None = None,
        on_left_click: ItemHandler | None = None,
        on_right_click: ItemHandler | None = None,
    ) -> None:
        super().__init_subclass__()
        passed: dict[str, Any] = {
            'key': key,
            'name': name,
            'lore': lore,
            'count': count,
            'enchantments': enchantments,
            'unbreakable': unbreakable,
            'damage': damage,
            'color': color,
            'skull_data': skull_data,
            'is_cookie_item': is_cookie_item,
            'hide_all_flags': hide_all_flags,
            'hide_enchantments_flag': hide_enchantments_flag,
            'hide_modifiers_flag': hide_modifiers_flag,
            'hide_unbreakable_flag': hide_unbreakable_flag,
            'hide_additional_flag': hide_additional_flag,
            'hide_dye_flag': hide_dye_flag,
        }
        defaults = dict(cls.__htsw_item_defaults__)
        defaults.update(
            {k: v for k, v in passed.items() if not isinstance(v, _MissingType)},
        )
        cls.__htsw_item_defaults__ = defaults
        cls.__htsw_name__ = cls.__name__
        if 'key' not in defaults:
            raise TypeError(
                f'Item subclass "{cls.__name__}" must specify a key, e.g. '
                f'class {cls.__name__}(Item, key="blaze_rod"): ...',
            )
        cls._register_importable(on_click, on_left_click, on_right_click)

    @classmethod
    def _register_importable(
        cls,
        on_click: ItemHandler | None,
        on_left_click: ItemHandler | None,
        on_right_click: ItemHandler | None,
    ) -> None:
        both_fn = on_click
        left_fn = on_left_click
        right_fn = on_right_click
        for value in vars(cls).values():
            tag = getattr(value, '__htsw_click__', None)
            if tag == 'both':
                both_fn = value
            elif tag == 'left':
                left_fn = value
            elif tag == 'right':
                right_fn = value

        left_fn, right_fn = _resolve_click_handlers(both_fn, left_fn, right_fn)
        _register_item_instance_importable(cls.__name__, cls(), left_fn, right_fn)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Item):
            return False
        return vars(self) == vars(other)

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

        return Item(cast(ALL_ITEM_KEYS, key), **options)

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
                        .put('lvl', NBTShort(enchantment.level or 1))
                        .put('id', NBTShort(ENCHANTMENT_TO_ID[enchantment.name]))
                        for enchantment in self.enchantments
                    ],
                ),
            )

        if self.unbreakable:
            tags.put('Unbreakable', NBTByte(1))

        hide_flags: int = min(
            sum(value for flag, value in HIDE_FLAGS.items() if getattr(self, flag)),
            HIDE_FLAGS['hide_all_flags'],
        )
        if hide_flags:
            tags.put('HideFlags', NBTInt(hide_flags))

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

        if not extra_attributes.is_empty():
            tags.put('ExtraAttributes', extra_attributes)

        if not tags.is_empty():
            result.put('tag', tags)

        return result

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
        key: ALL_ITEM_KEYS | _MissingType = MISSING,
        *,
        name: str | None | _MissingType = MISSING,
        lore: str | None | _MissingType = MISSING,
        count: int | _MissingType = MISSING,
        enchantments: list[Enchantment] | None | _MissingType = MISSING,
        unbreakable: bool | _MissingType = MISSING,
        damage: int | _MissingType = MISSING,
        color: ColorType | _MissingType = MISSING,
        skull_data: NBTCompound | None | _MissingType = MISSING,
        is_cookie_item: bool | _MissingType = MISSING,
        hide_all_flags: bool | _MissingType = MISSING,
        hide_enchantments_flag: bool | _MissingType = MISSING,
        hide_modifiers_flag: bool | _MissingType = MISSING,
        hide_unbreakable_flag: bool | _MissingType = MISSING,
        hide_additional_flag: bool | _MissingType = MISSING,
        hide_dye_flag: bool | _MissingType = MISSING,
    ) -> 'Item':
        """Returns a copy of the item, overriding only the given values."""
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
            'hide_all_flags': hide_all_flags,
            'hide_enchantments_flag': hide_enchantments_flag,
            'hide_modifiers_flag': hide_modifiers_flag,
            'hide_unbreakable_flag': hide_unbreakable_flag,
            'hide_additional_flag': hide_additional_flag,
            'hide_dye_flag': hide_dye_flag,
        }
        resolved = {
            field: getattr(self, field) if isinstance(value, _MissingType) else value
            for field, value in overrides.items()
        }
        return Item(self.key if isinstance(key, _MissingType) else key, **resolved)

    def anonymous_path(self) -> str:
        """Relative .snbt path for this item, registering it with the active
        project so the file gets written on export."""
        from ..container import get_current_container

        container = get_current_container()
        if container.project is not None:
            root_relpath = container.project.item_path(self)
            return container.project.item_reference(root_relpath)
        snbt = self.into_snbt()
        suffix = hashlib.md5(snbt.encode()).hexdigest()[:8]
        return f'items/{into_kebab(self.key)}-{suffix}.snbt'


def _register_item_instance_importable(
    name: str,
    item: 'Item',
    left_fn: 'ItemHandler | None',
    right_fn: 'ItemHandler | None',
) -> None:
    from ..block import NamedBlock
    from ..container import get_current_container
    from ..importable import ItemImportable, call_with_args

    container = get_current_container()
    left_block = right_block = None
    if left_fn is not None:
        left_block = NamedBlock(
            f'{name} left',
            callback=lambda fn=left_fn: call_with_args(fn, item),
        )
        container.add_block(left_block)
    if right_fn is not None:
        right_block = NamedBlock(
            f'{name} right',
            callback=lambda fn=right_fn: call_with_args(fn, item),
        )
        container.add_block(right_block)

    container.register_importable(
        ItemImportable(name=name, item=item, left=left_block, right=right_block),
    )


def normalize_item(value: 'Item | type[Item]') -> Item:
    if isinstance(value, type):
        if not issubclass(value, Item):
            raise TypeError(f'Expected an Item subclass, got {value!r}')
        return value()
    if isinstance(value, Item):
        return value
    raise TypeError(f'Expected an Item or Item subclass, got {value!r}')


def item_action_reference(value: 'Item | type[Item]') -> str:
    """How an item is referenced from an action: a declared subclass by its
    htsw name, an interactive instance by its importable name, a plain instance
    by its .snbt path."""
    if isinstance(value, type):
        if not issubclass(value, Item):
            raise TypeError(f'Expected an Item subclass, got {value!r}')
        name = value.__htsw_name__
        if name is None:
            raise TypeError(f'{value!r} is not a declared item importable')
        return name
    if isinstance(value, Item):
        if getattr(value, '_importable_name', None) is not None:
            return value._importable_name  # type: ignore[return-value]
        return value.anonymous_path()
    raise TypeError(f'Expected an Item or Item subclass, got {value!r}')
