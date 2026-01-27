from ..types import ALL_ENCHANTMENTS


__all__ = ('Enchantment',)


class Enchantment:
    name: ALL_ENCHANTMENTS
    level: int | None

    def __init__(
        self,
        name: ALL_ENCHANTMENTS,
        level: int | None = None,
    ) -> None:
        self.name = name
        self.level = level

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Enchantment):
            return NotImplemented
        return self.name == other.name and self.level == other.level
