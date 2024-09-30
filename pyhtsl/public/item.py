from ..writer import HERE, HTSL_IMPORTS_FOLDER
from ..types import NON_SPECIAL_ITEM_KEYS, DAMAGEABLE_ITEM_KEYS, LEATHER_ARMOR_KEYS, ALL_ITEM_KEYS, ALL_ENCHANTMENTS, ENCHANTMENT_TO_ID
from .enchantment import Enchantment

import json
import re
from enum import Enum
import hashlib
import difflib

from typing import TypedDict, overload, Iterable, Optional, Any, Callable


__all__ = (
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


class DataTypeCallback:
    callback: Callable[[Any], str]
    def __init__(self, callback: Callable[[Any], str]) -> None:
        self.callback = callback

    def __call__(self, value: Any) -> str:
        return self.callback(value)


class DataType(Enum):
    byte = DataTypeCallback(lambda x: f'{x}b')
    short = DataTypeCallback(lambda x: f'{x}s')
    integer = DataTypeCallback(lambda x: f'{x}')
    string = DataTypeCallback(lambda x: '\\"' + x.replace('"', '\\"') + '\\"')


SAVED_CACHE: dict[str, str] = {}


class Item:
    _key: str
    extras: dict[str, Any]

    @overload
    def __init__(
        self,
        key: NON_SPECIAL_ITEM_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str] = None,
        count: int = 1,
        enchantments: Optional[list[Enchantment]] = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_additional_flag: bool = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        key: DAMAGEABLE_ITEM_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str] = None,
        count: int = 1,
        enchantments: Optional[list[Enchantment]] = None,
        unbreakable: bool = False,
        damage: int = 0,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_unbreakable_flag: bool = False,
        hide_additional_flag: bool = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        key: LEATHER_ARMOR_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str] = None,
        count: int = 1,
        enchantments: Optional[list[Enchantment]] = None,
        unbreakable: bool = False,
        damage: int = 0,
        color: Optional[int | str | tuple[int, int, int]] = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_unbreakable_flag: bool = False,
        hide_additional_flag: bool = False,
        hide_dye_flag: bool = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        key: ALL_ITEM_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str] = None,
        count: int = 1,
        enchantments: Optional[list[Enchantment]] = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_additional_flag: bool = False,
        **extras: Any,
    ) -> None:
        ...

    def __init__(
        self,
        key: ALL_ITEM_KEYS,
        **extras: Any,
    ) -> None:
        self._key = key
        self.extras = extras
        self.key_check()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Item):
            return False
        return self._key == other._key and self.extras == other.extras

    def as_title(self) -> str:
        return self.key_check()['title']

    def replace_placeholders(self, text: str) -> str:
        return re.sub(r'&([0-9a-fk-or])', r'§\1', text)

    def one_lineify(
        self,
        data: dict[
            str, tuple[int | str | list[int] | list[str] | list[dict[str, int]], DataType] | dict[
                str, tuple[int | str | list[int] | list[str] | list[dict[str, int]], DataType] | dict[
                    str, tuple[int | str | list[int] | list[str] | list[dict[str, int]], DataType]
                ]
            ]
        ] | tuple[int | str | list[int] | list[str] | list[dict[str, int]], DataType],
    ) -> str:
        if isinstance(data, tuple):
            left, right = data
            if isinstance(left, (int, str)):
                return right.value(left)
            else:
                inside = type(left[0])
                if inside is dict:
                    mappings: list[dict[str, int]] = left  # type: ignore
                    return '[' + ','.join(f'{i}:{{' + ','.join(f'{k}:{right.value(v)}' for k, v in item.items()) + '}' for i, item in enumerate(mappings)) + ']'
                else:
                    return '[' + ','.join(f'{i}:{right.value(x)}' for i, x in enumerate(left)) + ']'
        return '{' + ','.join(f'{k}:{self.one_lineify(v)}' for k, v in data.items()) + '}'  # type: ignore

    def fetch_line(self, item: ItemJsonData) -> str:
        extras_copy = self.extras.copy()
        # cant be arsed to annotate the following because look at `one_lineify`
        data = {
            'id': (item['name'], DataType.string),
            'Count': (extras_copy.pop('count', 1), DataType.byte),
            'tag': {},
            'Damage': (item['data_value'], DataType.short),
        }
        if item['can_be_damaged']:
            data['Damage'] = (extras_copy.pop('damage', 0), DataType.short)
        tags = data['tag']

        enchantments: Optional[list[Enchantment]] = extras_copy.pop('enchantments', None)
        if enchantments is not None:
            tags['ench'] = ([{
                'lvl': enchantment.level or 1,
                'id': ENCHANTMENT_TO_ID[enchantment.name],
            } for enchantment in enchantments], DataType.short)

        unbreakable: int = int(extras_copy.pop('unbreakable', False))
        if unbreakable:
            if not item['can_be_damaged']:
                raise ValueError(f'Item "{self._key}" cannot be unbreakable.')
            tags['Unbreakable'] = (1, DataType.byte)

        hide_flags: int = min(sum(
            value for key, value in HIDE_FLAGS.items() if extras_copy.pop(key, False)
        ), HIDE_FLAGS['hide_all_flags'])
        if hide_flags:
            tags['HideFlags'] = (hide_flags, DataType.integer)

        lore: Optional[str] = extras_copy.pop('lore', None)
        if lore is not None:
            lore = self.replace_placeholders(lore)
            display = tags.setdefault('display', {})
            display['Lore'] = (lore.split('\n'), DataType.string)

        name: Optional[str] = extras_copy.pop('name', None)
        if name is not None:
            name = self.replace_placeholders(name)
            display = tags.setdefault('display', {})
            display['Name'] = (name, DataType.string)

        color: Optional[int | str | tuple[int, int, int]] = extras_copy.pop('color', None)
        if color is not None:
            if not isinstance(color, (int, str, tuple)):
                raise ValueError(f'Invalid color type: {type(color)}')
            if isinstance(color, str):
                color = int(color.removeprefix('#'), 16)
            elif isinstance(color, tuple):
                color = color[0] << 16 | color[1] << 8 | color[2]
            display = tags.setdefault('display', {})
            display['color'] = (color, DataType.integer)

        if not tags:
            del data['tag']

        if extras_copy:
            print(f'\x1b[38;2;255;0;0mIgnoring unused keys whilst saving "{self._key}": {', '.join(extras_copy.keys())}\x1b[0m')

        return '{"item": "' + self.one_lineify(data) + '"}'

    def key_check(self) -> ItemJsonData:
        item = ITEMS.get(self._key, None)
        if item is None:
            closest = difflib.get_close_matches(self._key.lower(), ITEMS.keys(), n=1, cutoff=0.0)[0]
            raise ValueError(
                f'Invalid item key: \x1b[38;2;255;0;0m{self._key}\x1b[0m. Did you mean \x1b[38;2;0;255;0m{closest}\x1b[0m?\nHave you already saved this in your imports folder? Do not create an Item, use the string "{self._key}" instead.'
            )
        return item

    def copy(self) -> 'Item':
        return Item(self._key, **self.extras)  # type: ignore

    def save(self) -> str:
        item = self.key_check()
        line = self.fetch_line(item)
        cached = SAVED_CACHE.get(line, None)
        if cached is not None:
            print(f'Using cached \033[38;2;0;255;0m{item["title"]}\033[0m as \x1b[38;2;255;0;0m{cached}\x1b[0m.')
            return cached
        suffix = hashlib.md5(line.encode()).hexdigest()[:8]
        name = f'_{self._key}_{suffix}'
        path = HTSL_IMPORTS_FOLDER / f'{name}.json'
        with path.open('w', encoding='utf-8') as file:
            file.write(line)
        SAVED_CACHE[line] = name
        print(
            f'Successfully saved \033[38;2;0;255;0m{item["title"]}\033[0m as \x1b[38;2;255;0;0m{name}\x1b[0m to be used in your script:'
            f'\n  \033[38;2;0;255;0m+\033[0m {path.absolute()}'
        )
        return name

    @property
    def key(self) -> str:
        return self._key

    @key.setter
    def key(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f'Expected str, got {type(value).__name__}')
        self._key = value
        self.key_check()

    @property
    def name(self) -> Optional[str]:
        return self.extras.get('name', None)

    @name.setter
    def name(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError(f'Expected str, got {type(value).__name__}')
        self.extras['name'] = value

    @property
    def lore(self) -> Optional[str]:
        return self.extras.get('lore', None)

    @lore.setter
    def lore(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError(f'Expected str, got {type(value).__name__}')
        self.extras['lore'] = value

    @property
    def count(self) -> int:
        return self.extras.get('count', 1)

    @count.setter
    def count(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError(f'Expected int, got {type(value).__name__}')
        self.extras['count'] = value

    @property
    def enchantments(self) -> Optional[list[Enchantment]]:
        return self.extras.get('enchantments', None)

    @enchantments.setter
    def enchantments(self, value: Optional[list[Enchantment]]) -> None:
        if value is not None and not isinstance(value, list):
            raise TypeError(f'Expected list, got {type(value).__name__}')
        self.extras['enchantments'] = value
