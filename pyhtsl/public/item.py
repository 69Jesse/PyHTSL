from ..writer import HERE, HTSL_IMPORTS_FOLDER
from ..types import (
    NON_SPECIAL_ITEM_KEYS,
    DAMAGEABLE_ITEM_KEYS,
    LEATHER_ARMOR_KEYS,
    COOKIE_ITEM_KEY,
    PLAYER_SKULL_ITEM_KEY,
    ALL_ITEM_KEYS,
    ENCHANTMENT_TO_ID,
)
from .enchantment import Enchantment
from ..nbt import NBTByte, NBTCompound, NBTInt, NBTList, NBTShort, NBTString

import json
import re
import hashlib
import difflib

from typing import TypedDict, overload, Any


__all__ = ('Item',)


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


HIDE_FLAGS: dict[str, int] = {
    'hide_enchantments_flag': 1,
    'hide_modifiers_flag': 2,
    'hide_unbreakable_flag': 4,
    # 'hide_can_destroy_flag': 8,    # Not sure what these do and if theyre actually implemented, if they are let me know..
    # 'hide_can_place_on_flag': 16,  #
    'hide_additional_flag': 32,
    'hide_dye_flag': 64,
}
HIDE_FLAGS['hide_all_flags'] = max(HIDE_FLAGS.values()) * 2 - 1


def replace_formatting(text: str) -> str:
    return re.sub(r'&([0-9a-fk-or])', r'§\1', text)


def remove_formatting(text: str) -> str:
    return re.sub(r'[&§][0-9a-fk-or]', '', text)


COLOR_MAPPINGS: dict[str, int] = {
    '§0': 0x000000,
    '§1': 0x0000AA,
    '§2': 0x00AA00,
    '§3': 0x00AAAA,
    '§4': 0xAA0000,
    '§5': 0xAA00AA,
    '§6': 0xFFAA00,
    '§7': 0xAAAAAA,
    '§8': 0x555555,
    '§9': 0x5555FF,
    '§a': 0x55FF55,
    '§b': 0x55FFFF,
    '§c': 0xFF5555,
    '§d': 0xFF55FF,
    '§e': 0xFFFF55,
    '§f': 0xFFFFFF,
}


def ansi_color(
    text: str,
    color: int,
    *,
    reset: bool = True,
) -> str:
    return (
        f'\033[38;2;{color >> 16 & 0xFF};{color >> 8 & 0xFF};{color & 0xFF}m{text}'
        + ('\033[0m' if reset else '')
    )


def formatting_to_ansi(text: str) -> str:
    text = replace_formatting(text)
    def replace(match: re.Match) -> str:
        key = match.group()
        if key == '§r':
            return '\033[0m'
        color = COLOR_MAPPINGS.get(key, None)
        if color is None:
            return ''
        return ansi_color('', color, reset=False)

    return re.sub(r'§[0-9a-fk-or]', replace, text) + '\033[0m'


SAVED_CACHE: dict[str, str] = {}


class Item:
    _key: ALL_ITEM_KEYS
    extras: dict[str, Any]

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
        color: int | str | tuple[int, int, int] | None = None,
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
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_additional_flag: bool = False,
        **extras: Any,
    ) -> None: ...

    def __init__(
        self,
        key: ALL_ITEM_KEYS,
        **extras: Any,
    ) -> None:
        self._key = key
        self.extras = extras
        self._get_item_data()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Item):
            return False
        return self._key == other._key and self.extras == other.extras

    def get_item_name(self) -> str:
        return self._get_item_data()['title']

    def _as_json(self, data: ItemJsonData) -> str:
        extras_copy = self.extras.copy()

        tags = NBTCompound()
        compound = (
            NBTCompound()
            .put(
                'id',
                NBTString(data['name']),
            )
            .put(
                'Count',
                NBTByte(extras_copy.pop('count', 1)),
            )
            .put(
                'Damage',
                NBTShort(data['data_value']),
            )
        )

        if data['can_be_damaged']:
            compound.put('Damage', NBTShort(extras_copy.pop('damage', 0)))

        enchantments: list[Enchantment] | None = extras_copy.pop('enchantments', None)
        if enchantments is not None:
            tags.put(
                'ench',
                NBTList(
                    [
                        NBTCompound()
                        .put('lvl', NBTShort(enchantment.level or 1))
                        .put('id', NBTShort(ENCHANTMENT_TO_ID[enchantment.name]))
                        for enchantment in enchantments
                    ]
                ),
            )

        unbreakable: int = int(extras_copy.pop('unbreakable', False))
        if unbreakable:
            if not data['can_be_damaged']:
                raise ValueError(f'Item "{self._key}" cannot be unbreakable.')
            tags.put('Unbreakable', NBTByte(unbreakable))

        hide_flags: int = min(
            sum(
                value
                for key, value in HIDE_FLAGS.items()
                if extras_copy.pop(key, False)
            ),
            HIDE_FLAGS['hide_all_flags'],
        )
        if hide_flags:
            tags.put('HideFlags', NBTInt(hide_flags))

        display = NBTCompound()

        lore: str | None = extras_copy.pop('lore', None)
        if lore is not None:
            lore = replace_formatting(lore)
            display.put('Lore', NBTList([NBTString(line) for line in lore.split('\n')]))

        name: str | None = extras_copy.pop('name', None)
        if name is not None:
            name = replace_formatting(name)
            display.put('Name', NBTString(name))

        color: int | str | tuple[int, int, int] | None = extras_copy.pop('color', None)
        if color is not None:
            if not isinstance(color, (int, str, tuple)):
                raise ValueError(f'Invalid color type: {type(color)}')
            if isinstance(color, str):
                color = int(color.removeprefix('#'), 16)
            elif isinstance(color, tuple):
                color = color[0] << 16 | color[1] << 8 | color[2]
            display.put('color', NBTInt(color))

        skull_data: NBTCompound | None = extras_copy.pop('skull_data', None)
        if skull_data is not None:
            tags.put('SkullOwner', skull_data)

        if not display.is_empty():
            tags.put('display', display)

        extra_attributes = NBTCompound()

        interaction_data_key: str | None = extras_copy.pop('interaction_data_key', None)
        if interaction_data_key is not None:
            interact_data = (
                NBTCompound()
                .put('data', NBTString(interaction_data_key))
                .put('version', NBTInt(2))
            )
            extra_attributes.put('interact_data', interact_data)

        is_cookie_item: bool = extras_copy.pop('is_cookie_item', False)
        if is_cookie_item:
            extra_attributes.put('COOKIE_ITEM', NBTByte(1))

        if not extra_attributes.is_empty():
            tags.put('ExtraAttributes', extra_attributes)

        if not tags.is_empty():
            compound.put('tag', tags)

        if extras_copy:
            print(
                f'\x1b[38;2;255;0;0mIgnoring unused keys whilst saving "{self._key}": {", ".join(extras_copy.keys())}\x1b[0m'
            )

        return json.dumps(
            {
                'item': compound.to_snbt(),
            }
        )

    def _get_item_data(self) -> ItemJsonData:
        item = ITEMS.get(self._key, None)
        if item is None:
            closest = difflib.get_close_matches(
                self._key.lower(), ITEMS.keys(), n=1, cutoff=0.0
            )[0]
            raise ValueError(
                f'Invalid item key: \x1b[38;2;255;0;0m{self._key}\x1b[0m. Did you mean \x1b[38;2;0;255;0m{closest}\x1b[0m?\nHave you already saved this in your imports folder? Do not create an Item, use the string "{self._key}" instead.'
            )
        return item

    def copied(self) -> 'Item':
        return Item(self._key, **self.extras)  # type: ignore

    def _get_save_name(self, json_data: str) -> str:
        prefix: str | None = self.extras.get('name', None)
        if prefix is not None:
            prefix = re.sub(r'[&§][0-9a-fk-or]', '', prefix)
            prefix = prefix.lower().replace(' ', '_')
            prefix = re.sub(r'[^a-z0-9_]', '', prefix)
        if not prefix:
            prefix = self._key
        suffix = hashlib.md5(json_data.encode()).hexdigest()[:8]
        return f'_{prefix}_{suffix}'

    def save(self) -> str:
        data = self._get_item_data()
        json_data = self._as_json(data)
        cached = SAVED_CACHE.get(json_data, None)

        title = f'\033[38;2;0;255;0m{data["title"]}\033[0m'
        if self.count != 1:
            title = f'\033[38;2;0;191;255mx{self.count}\033[0m ' + title
        display_name = self.extras.get('name', None)
        if display_name is not None:
            title += f' ({formatting_to_ansi(display_name)})'

        if cached is not None:
            print(f'Using cached {title} as \x1b[38;2;255;0;0m{cached}\x1b[0m.')
            return cached

        name = self._get_save_name(json_data)
        path = HTSL_IMPORTS_FOLDER / f'{name}.json'
        path.write_text(json_data, encoding='utf-8')

        SAVED_CACHE[json_data] = name
        print(
            f'Successfully saved {title} as \x1b[38;2;255;0;0m{name}\x1b[0m to be used in your script:'
            f'\n  \033[38;2;0;255;0m+\033[0m {path.absolute()}'
        )
        return name

    @property
    def key(self) -> ALL_ITEM_KEYS:
        return self._key

    @key.setter
    def key(self, value: ALL_ITEM_KEYS) -> None:
        if not isinstance(value, str):
            raise TypeError(f'Expected str, got {type(value).__name__}')
        self._key = value
        self._get_item_data()

    def with_key(self, key: ALL_ITEM_KEYS) -> 'Item':
        """Returns a copy of the item with the specified key."""
        new_item = self.copied()
        new_item.key = key
        return new_item

    @property
    def name(self) -> str | None:
        return self.extras.get('name', None)

    @name.setter
    def name(self, value: str | None) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError(f'Expected str, got {type(value).__name__}')
        self.extras['name'] = value

    def with_name(self, name: str | None) -> 'Item':
        """Returns a copy of the item with the specified name."""
        new_item = self.copied()
        new_item.name = name
        return new_item

    @property
    def lore(self) -> str | None:
        return self.extras.get('lore', None)

    @lore.setter
    def lore(self, value: str | None) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError(f'Expected str, got {type(value).__name__}')
        self.extras['lore'] = value

    def with_lore(self, lore: str | None) -> 'Item':
        """Returns a copy of the item with the specified lore."""
        new_item = self.copied()
        new_item.lore = lore
        return new_item

    @property
    def count(self) -> int:
        return self.extras.get('count', 1)

    @count.setter
    def count(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError(f'Expected int, got {type(value).__name__}')
        self.extras['count'] = value

    def with_count(self, count: int) -> 'Item':
        """Returns a copy of the item with the specified count."""
        new_item = self.copied()
        new_item.count = count
        return new_item

    @property
    def enchantments(self) -> list[Enchantment] | None:
        return self.extras.get('enchantments', None)

    @enchantments.setter
    def enchantments(self, value: list[Enchantment] | None) -> None:
        if value is not None and not isinstance(value, list):
            raise TypeError(f'Expected list, got {type(value).__name__}')
        self.extras['enchantments'] = value

    def with_enchantments(self, enchantments: list[Enchantment] | None) -> 'Item':
        """Returns a copy of the item with the specified enchantments."""
        new_item = self.copied()
        new_item.enchantments = enchantments
        return new_item

    @property
    def interaction_data_key(self) -> str | None:
        return self.extras.get('interaction_data_key', None)

    @interaction_data_key.setter
    def interaction_data_key(self, value: str | None) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError(f'Expected str, got {type(value).__name__}')
        self.extras['interaction_data_key'] = value

    def with_interaction_data_key(self, key: str | None) -> 'Item':
        """Returns a copy of the item with the specified interaction data key."""
        new_item = self.copied()
        new_item.interaction_data_key = key
        return new_item
