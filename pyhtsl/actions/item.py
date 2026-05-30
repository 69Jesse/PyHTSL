import difflib
import hashlib
import json
from pathlib import Path
from typing import Any, TypedDict, cast, get_args, overload

from pyhtsl.utils.slug import into_slug

from ..config import HERE, get_htsl_import_folder
from ..nbt import NBT, NBTByte, NBTCompound, NBTInt, NBTList, NBTShort, NBTString
from ..types import (
    ALL_ENCHANTMENTS,
    ALL_ITEM_KEY_STRINGS,
    ALL_ITEM_KEYS,
    COOKIE_ITEM_KEY,
    DAMAGEABLE_ITEM_KEYS,
    ENCHANTMENT_TO_ID,
    LEATHER_ARMOR_KEYS,
    NON_SPECIAL_ITEM_KEYS,
    PLAYER_SKULL_ITEM_KEY,
    ColorType,
)
from ..utils.formatting import (
    formatting_to_ansi,
    normalize_formatting,
    remove_formatting,
)
from ..utils.log import log
from .enchantment import Enchantment

__all__ = (
    'normalize_item_key',
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
    # 'hide_can_destroy_flag': 8,    # Not sure what these do and if they're actually implemented, if they are let me know..
    # 'hide_can_place_on_flag': 16,  #
    'hide_additional_flag': 32,
    'hide_dye_flag': 64,
}
HIDE_FLAGS['hide_all_flags'] = max(HIDE_FLAGS.values()) * 2 - 1


SAVED_CACHE: dict[str, str] = {}


class _MissingType:
    __slots__ = ()


MISSING = _MissingType()


def normalize_item_key(key: ALL_ITEM_KEYS) -> str:
    if isinstance(key, str):
        return key
    return key[0]


class Item:
    key: ALL_ITEM_KEY_STRINGS
    name: str | None
    lore: str | None
    count: int
    enchantments: list[Enchantment] | None
    interaction_data_key: str | None
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

    @overload
    def __init__(
        self,
        key: NON_SPECIAL_ITEM_KEYS,
        *,
        name: str | None = None,
        lore: str | None = None,
        count: int = 1,
        enchantments: list[Enchantment] | None = None,
        interaction_data_key: str | None = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_additional_flag: bool = False,
    ) -> None: ...

    @overload
    def __init__(
        self,
        key: DAMAGEABLE_ITEM_KEYS,
        *,
        name: str | None = None,
        lore: str | None = None,
        count: int = 1,
        enchantments: list[Enchantment] | None = None,
        interaction_data_key: str | None = None,
        unbreakable: bool = False,
        damage: int = 0,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_unbreakable_flag: bool = False,
        hide_additional_flag: bool = False,
    ) -> None: ...

    @overload
    def __init__(
        self,
        key: LEATHER_ARMOR_KEYS,
        *,
        name: str | None = None,
        lore: str | None = None,
        count: int = 1,
        enchantments: list[Enchantment] | None = None,
        interaction_data_key: str | None = None,
        unbreakable: bool = False,
        damage: int = 0,
        color: ColorType = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_unbreakable_flag: bool = False,
        hide_additional_flag: bool = False,
        hide_dye_flag: bool = False,
    ) -> None: ...

    @overload
    def __init__(
        self,
        key: COOKIE_ITEM_KEY,
        *,
        name: str | None = None,
        lore: str | None = None,
        count: int = 1,
        enchantments: list[Enchantment] | None = None,
        interaction_data_key: str | None = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_additional_flag: bool = False,
        is_cookie_item: bool = False,
    ) -> None: ...

    @overload
    def __init__(
        self,
        key: PLAYER_SKULL_ITEM_KEY,
        *,
        name: str | None = None,
        lore: str | None = None,
        count: int = 1,
        enchantments: list[Enchantment] | None = None,
        interaction_data_key: str | None = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_additional_flag: bool = False,
        skull_data: NBTCompound | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        key: ALL_ITEM_KEYS,
        *,
        name: str | None = None,
        lore: str | None = None,
        count: int = 1,
        enchantments: list[Enchantment] | None = None,
        interaction_data_key: str | None = None,
        unbreakable: bool = False,
        damage: int = 0,
        color: ColorType = None,
        skull_data: NBTCompound | None = None,
        is_cookie_item: bool = False,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_unbreakable_flag: bool = False,
        hide_additional_flag: bool = False,
        hide_dye_flag: bool = False,
    ) -> None: ...

    def __init__(
        self,
        key: ALL_ITEM_KEYS,
        *,
        name: str | None = None,
        lore: str | None = None,
        count: int = 1,
        enchantments: list[Enchantment] | None = None,
        interaction_data_key: str | None = None,
        unbreakable: bool = False,
        damage: int = 0,
        color: ColorType = None,
        skull_data: NBTCompound | None = None,
        is_cookie_item: bool = False,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_unbreakable_flag: bool = False,
        hide_additional_flag: bool = False,
        hide_dye_flag: bool = False,
    ) -> None:
        if isinstance(key, tuple):
            string_key, packed = key
            if string_key in get_args(LEATHER_ARMOR_KEYS):
                if color is not None:
                    log(
                        '\x1b[38;2;255;0;0mcolor was given both in the key tuple and as a keyword argument; the tuple takes precedence\x1b[0m'
                    )
                color = cast(ColorType, packed)
            elif string_key in get_args(PLAYER_SKULL_ITEM_KEY):
                if skull_data is not None:
                    log(
                        '\x1b[38;2;255;0;0mskull_data was given both in the key tuple and as a keyword argument; the tuple takes precedence\x1b[0m'
                    )
                skull_data = cast('NBTCompound | None', packed)
            else:
                raise ValueError(f'Item key {string_key!r} does not take a tuple value')
            key = string_key

        self.key = cast(ALL_ITEM_KEY_STRINGS, key)
        self.name = name
        self.lore = lore
        self.count = count
        self.enchantments = enchantments
        self.interaction_data_key = interaction_data_key
        self.unbreakable = unbreakable
        self.damage = damage
        self.color = color
        self.skull_data = skull_data
        self.is_cookie_item = is_cookie_item
        self.hide_all_flags = hide_all_flags
        self.hide_enchantments_flag = hide_enchantments_flag
        self.hide_modifiers_flag = hide_modifiers_flag
        self.hide_unbreakable_flag = hide_unbreakable_flag
        self.hide_additional_flag = hide_additional_flag
        self.hide_dye_flag = hide_dye_flag
        self._get_item_data()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Item):
            return False
        return vars(self) == vars(other)

    @classmethod
    def from_name(cls, name: str) -> 'Item':
        folder = get_htsl_import_folder()
        path = folder / name
        if path.suffix:
            return cls.from_path(path)
        for suffix in ('.json', '.snbt'):
            candidate = path.with_suffix(suffix)
            if candidate.exists():
                return cls.from_path(candidate)
        return cls.from_path(path.with_suffix('.json'))

    @classmethod
    def from_path(cls, path: Path) -> 'Item':
        if path.suffix == '.json':
            data = json.loads(path.read_text(encoding='utf-8'))
            return cls.from_snbt(data['item'])
        if path.suffix == '.snbt':
            return cls.from_snbt(path.read_text(encoding='utf-8'))
        raise ValueError(f'Unsupported item file type: {path.suffix}')

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
                    f'Could not resolve an item key from id {name!r} with data value {damage_value}.'
                )

        count = nbt.get('Count')
        if count is not None and count.value != 1:
            options['count'] = count.value

        tags = nbt.get('tag')
        if isinstance(tags, NBTCompound):
            cls._extract_tags(tags, options)

        return cls(cast(ALL_ITEM_KEYS, key), **options)

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
            interact = extra_attributes.get('interact_data')
            if isinstance(interact, NBTCompound):
                data = interact.get('data')
                if data is not None:
                    options['interaction_data_key'] = data.value
            if extra_attributes.get('COOKIE_ITEM') is not None:
                options['is_cookie_item'] = True

    def get_item_name(self) -> str:
        return self._get_item_data()['title']

    def into_nbt(self, data: ItemJsonData | None = None) -> NBTCompound[NBT]:
        if data is None:
            data = self._get_item_data()

        result: NBTCompound[NBT] = NBTCompound(
            {
                'id': NBTString(data['name']),
                'Count': NBTByte(self.count),
                'Damage': NBTShort(data['data_value']),
            }
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
                    ]
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

        if self.interaction_data_key is not None:
            interact_data = (
                NBTCompound()
                .put('data', NBTString(self.interaction_data_key))
                .put('version', NBTInt(2))
            )
            extra_attributes.put('interact_data', interact_data)

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
                f'Invalid item key: \x1b[38;2;255;0;0m{self.key}\x1b[0m. Did you mean \x1b[38;2;0;255;0m{closest}\x1b[0m?\nHave you already saved this in your imports folder? Do not create an Item, use the string "{self.key}" instead.'
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
        interaction_data_key: str | None | _MissingType = MISSING,
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
            'interaction_data_key': interaction_data_key,
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
            field: getattr(self, field) if value is MISSING else value
            for field, value in overrides.items()
        }
        return Item(self.key if isinstance(key, _MissingType) else key, **resolved)

    def _get_save_name(self, snbt: str) -> str:
        prefix = into_slug(f'{self.key}_{remove_formatting(self.name or "")}')

        suffix = hashlib.md5(snbt.encode()).hexdigest()[:8]
        return f'_{len(SAVED_CACHE) % 1000:03}_{prefix}_{suffix}'

    def save(self) -> str:
        data = self._get_item_data()
        snbt = self.into_nbt(data).into_snbt()
        cached = SAVED_CACHE.get(snbt, None)

        title = f'\033[38;2;0;255;0m{data["title"]}\033[0m'
        if self.count != 1:
            title = f'\033[38;2;0;191;255mx{self.count}\033[0m ' + title
        display_name = self.name
        if display_name is not None:
            title += f' ({formatting_to_ansi(display_name)})'

        if cached is not None:
            log(f'Using cached {title} as \x1b[38;2;255;0;0m{cached}\x1b[0m.')
            return cached

        name = self._get_save_name(snbt)
        path = get_htsl_import_folder() / f'{name}.json'

        content = json.dumps({'item': snbt})
        path.write_text(content, encoding='utf-8')

        SAVED_CACHE[snbt] = name
        log(
            f'Successfully saved {title} as \x1b[38;2;255;0;0m{name}\x1b[0m to be used in your script:'
            f'\n  \033[38;2;0;255;0m+\033[0m {path.absolute()}'
        )
        return name
