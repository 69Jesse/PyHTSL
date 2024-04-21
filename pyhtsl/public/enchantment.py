
from typing import Literal, Optional


__all__ = (
    'ALL_POSSIBLE_ENCHANTMENTS',
    'ENCHANTMENT_TO_ID',
    'Enchantment'
)


ALL_POSSIBLE_ENCHANTMENTS = Literal[
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
    'luck_of_the_sea',
    'lure',
]


ENCHANTMENT_TO_ID: dict[ALL_POSSIBLE_ENCHANTMENTS, int] = {
    'protection': 0,
    'fire_protection': 1,
    'feather_falling': 2,
    'blast_protection': 3,
    'projectile_protection': 4,
    'respiration': 5,
    'aqua_affinity': 6,
    'thorns': 7,
    'depth_strider': 8,
    'sharpness': 16,
    'smite': 17,
    'bane_of_arthropods': 18,
    'knockback': 19,
    'fire_aspect': 20,
    'looting': 21,
    'efficiency': 32,
    'silk_touch': 33,
    'unbreaking': 34,
    'fortune': 35,
    'power': 48,
    'punch': 49,
    'flame': 50,
    'infinity': 51,
    'luck_of_the_sea': 61,
    'lure': 62,
}


class Enchantment:
    name: ALL_POSSIBLE_ENCHANTMENTS
    level: Optional[int]
    def __init__(
        self,
        name: ALL_POSSIBLE_ENCHANTMENTS,
        level: Optional[int] = None,
    ) -> None:
        self.name = name
        self.level = level
