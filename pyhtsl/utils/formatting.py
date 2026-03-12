import re
from typing import Literal

__all__ = (
    'normalize_formatting',
    'remove_formatting',
    'formatting_to_ansi',
)

FORMATTING_REGEX: re.Pattern[str] = re.compile(r'[&§][0-9a-fk-or]')


def normalize_formatting(text: str, *, symbol: Literal['&', '§'] = '§') -> str:
    return FORMATTING_REGEX.sub(f'{symbol}\\1', text)


def remove_formatting(text: str) -> str:
    return FORMATTING_REGEX.sub('', text)


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
    text = normalize_formatting(text)

    def replace(match: re.Match) -> str:
        key = match.group()
        if key == '§r':
            return '\033[0m'
        color = COLOR_MAPPINGS.get(key, None)
        if color is None:
            return ''
        return ansi_color('', color, reset=False)

    return FORMATTING_REGEX.sub(replace, text) + '\033[0m'
