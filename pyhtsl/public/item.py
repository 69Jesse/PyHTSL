from ..writer import HERE, HTSL_IMPORTS_FOLDER
from ..types import NON_SPECIAL_ITEM_KEYS, DAMAGEABLE_ITEM_KEYS, LEATHER_ARMOR_KEYS, ALL_POSSIBLE_ITEM_KEYS, ALL_POSSIBLE_ENCHANTMENTS, ENCHANTMENT_TO_ID
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


EnchantmentsType = dict[Enchantment | ALL_POSSIBLE_ENCHANTMENTS, int] | Iterable[Enchantment | ALL_POSSIBLE_ENCHANTMENTS] | Enchantment | ALL_POSSIBLE_ENCHANTMENTS


SAVED_CACHE: dict[str, str] = {}


class Item:
    key: str
    extras: dict[str, Any]

    @overload
    def __init__(
        self,
        key: NON_SPECIAL_ITEM_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str | Iterable[str]] = None,
        count: int = 1,
        enchantments: Optional[EnchantmentsType] = None,
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
        lore: Optional[str | Iterable[str]] = None,
        count: int = 1,
        enchantments: Optional[EnchantmentsType] = None,
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
        lore: Optional[str | Iterable[str]] = None,
        count: int = 1,
        enchantments: Optional[EnchantmentsType] = None,
        unbreakable: bool = False,
        damage: int = 0,
        color: int | str | tuple[int, int, int] = 0,
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
        key: ALL_POSSIBLE_ITEM_KEYS,
        *,
        name: Optional[str] = None,
        lore: Optional[str | Iterable[str]] = None,
        count: int = 1,
        enchantments: Optional[EnchantmentsType] = None,
        hide_all_flags: bool = False,
        hide_enchantments_flag: bool = False,
        hide_modifiers_flag: bool = False,
        hide_additional_flag: bool = False,
        **extras: Any,
    ) -> None:
        ...

    def __init__(
        self,
        key: ALL_POSSIBLE_ITEM_KEYS,
        **extras: Any,
    ) -> None:
        self.key = key
        self.extras = extras
        self.key_check()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Item):
            return False
        return self.key == other.key and self.extras == other.extras

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

        enchantments: Optional[EnchantmentsType] = extras_copy.pop('enchantments', None)
        if enchantments is not None:
            if isinstance(enchantments, str):
                enchantments = Enchantment(enchantments)
            if isinstance(enchantments, Enchantment):
                enchantments = [enchantments]
            if isinstance(enchantments, dict):
                tags['ench'] = ([{
                    'lvl': value,
                    'id': ENCHANTMENT_TO_ID[key if isinstance(key, str) else key.name],
                } for key, value in enchantments.items()], DataType.short)
            else:
                tags['ench'] = ([{
                    'lvl': 1 if isinstance(enchantment, str) else enchantment.level or 1,
                    'id': ENCHANTMENT_TO_ID[enchantment if isinstance(enchantment, str) else enchantment.name],
                } for enchantment in enchantments], DataType.short)

        unbreakable: int = int(extras_copy.pop('unbreakable', False))
        if unbreakable:
            if not item['can_be_damaged']:
                raise ValueError(f'Item "{self.key}" cannot be unbreakable.')
            tags['Unbreakable'] = (1, DataType.byte)

        hide_flags: int = min(sum(
            value for key, value in HIDE_FLAGS.items() if extras_copy.pop(key, False)
        ), HIDE_FLAGS['hide_all_flags'])
        if hide_flags:
            tags['HideFlags'] = (hide_flags, DataType.integer)

        lore: Optional[str | Iterable[str]] = extras_copy.pop('lore', None)
        if lore is not None:
            if not isinstance(lore, str):
                lore = '\n'.join(lore)
            if lore:
                lore = self.replace_placeholders(lore)
                display = tags.setdefault('display', {})
                display['Lore'] = (lore.split('\n'), DataType.string)

        name: Optional[str] = extras_copy.pop('name', None)
        if name is not None:
            name = self.replace_placeholders(name)
            display = tags.setdefault('display', {})
            display['Name'] = (name, DataType.string)

        if not tags:
            del data['tag']

        if extras_copy:
            print(f'Unused keys: {", ".join(extras_copy.keys())}')

        return '{"item": "' + self.one_lineify(data) + '"}'

    def key_check(self) -> ItemJsonData:
        item = ITEMS.get(self.key, None)
        if item is None:
            closest = difflib.get_close_matches(self.key.lower(), ITEMS.keys(), n=1, cutoff=0.0)[0]
            raise ValueError(
                f'Invalid item key: \x1b[38;2;255;0;0m{self.key}\x1b[0m. Did you mean \x1b[38;2;0;255;0m{closest}\x1b[0m?\nYou\'ve already saved this in your imports folder? Do not create an Item, use the string "{self.key}" instead.'
            )
        return item

    def save(self) -> str:
        item = self.key_check()
        line = self.fetch_line(item)
        cached = SAVED_CACHE.get(line, None)
        if cached is not None:
            print(f'Using cached \x1b[38;2;0;255;0m{item["title"]}\x1b[0m as \x1b[38;2;255;0;0m{cached}\x1b[0m.')
            return cached
        suffix = hashlib.md5(line.encode()).hexdigest()[:8]
        name = f'_{self.key}_{suffix}'
        path = HTSL_IMPORTS_FOLDER / f'{name}.json'
        with path.open('w', encoding='utf-8') as file:
            file.write(line)
        SAVED_CACHE[line] = name
        print(f'Successfully saved \x1b[38;2;0;255;0m{item["title"]}\x1b[0m as \x1b[38;2;255;0;0m{name}\x1b[0m to be used in your script. Written it to\n{path.absolute()}')
        return name
