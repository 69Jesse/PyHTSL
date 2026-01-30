from ..editable import Editable

import re


__all__ = (
    'replace_formatting',
    'remove_formatting',
    'formatting_to_ansi',
    'get_placeholder_parts',
    'round_double',
)


REPLACE_FORMATTING_REGEX = re.compile(r'&([0-9a-fk-or])')


def replace_formatting(text: str) -> str:
    return REPLACE_FORMATTING_REGEX.sub(r'§\1', text)


REMOVE_FORMATTING_REGEX = re.compile(r'[&§][0-9a-fk-or]')


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


PLACEHOLDER_PARTS_REGEX = re.compile(r'%[^%]*%')


def get_placeholder_parts(value: str) -> list[str]:
    parts: list[str] = []
    last_index = 0

    for match in PLACEHOLDER_PARTS_REGEX.finditer(value):
        start, end = match.span()
        parts.append(value[last_index:start])
        parts.append(match.group())
        last_index = end

    parts.append(value[last_index:])

    return parts


def round_double(
    x: Editable,
    decimals: int,
) -> None:
    x = x.as_double()

    factor = 10**decimals
    x.value *= factor
    x.value += 0.5

    x.cast_to_long()
    x.cast_to_double()

    x.value /= factor
