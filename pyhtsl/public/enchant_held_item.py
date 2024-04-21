from ..writer import WRITER, LineType
from .enchantment import Enchantment, POSSIBLE_ENCHANTMENTS

from typing import Optional


__all__ = (
    'enchant_held_item',
)


def enchant_held_item(
    enchantment: POSSIBLE_ENCHANTMENTS | Enchantment,
    level: Optional[int] = None,
) -> None:
    if isinstance(enchantment, Enchantment):
        name = enchantment.name
        if level is None:
            level = enchantment.level
    else:
        name = enchantment
    if level is None:
        level = 1
    WRITER.write(
        f'enchant "{name}" {level}',
        LineType.miscellaneous,
    )
