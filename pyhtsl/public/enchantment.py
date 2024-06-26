from .types import ALL_POSSIBLE_ENCHANTMENTS

from typing import Optional


__all__ = (
    'Enchantment',
)


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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Enchantment):
            return NotImplemented
        return self.name == other.name and self.level == other.level
