from ..writer import WRITER, LineType
from ..types import ALL_ENCHANTMENTS
from .enchantment import Enchantment

from typing import Optional


__all__ = (
    'enchant_held_item',
)


def enchant_held_item(
    enchantment: ALL_ENCHANTMENTS | Enchantment,
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
