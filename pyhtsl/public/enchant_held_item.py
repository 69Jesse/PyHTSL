from ..writer import WRITER

from typing import Literal


__all__ = (
    'enchant_held_item',
)


def enchant_held_item(
    enchantment: Literal[
        'protection',
        'fire_protection',
        'feather_falling',
        'blast_protection',
        'projectile_protection',
        'respiration',
        'aqua_affinity',
        'thorns',
        'depth_strider',
        'sharpness',
        'smite',
        'bane_of_arthropods',
        'knockback',
        'fire_aspect',
        'looting',
        'efficiency',
        'silk_touch',
        'unbreaking',
        'fortune',
        'power',
        'punch',
        'flame',
        'infinity',
    ],
    level: int = 1,
) -> None:
    WRITER.write(f'enchant "{enchantment}" {level}')
