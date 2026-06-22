from typing import Self, final

from ..expression.expression import Expression
from ..types import ALL_ENCHANTMENTS
from .enchantment import Enchantment

__all__ = (
    'EnchantHeldItemExpression',
    'enchant_held_item',
)


@final
class EnchantHeldItemExpression(Expression):
    enchantment_name: str
    level: int

    def __init__(self, enchantment_name: str, level: int) -> None:
        self.enchantment_name = enchantment_name
        self.level = level

    def into_htsl(self) -> str:
        return f'enchant {self.inline_quoted(self.enchantment_name)} {self.inline(self.level)}'

    def cloned(self) -> Self:
        return self.__class__(enchantment_name=self.enchantment_name, level=self.level)

    def equals(self, other: object) -> bool:
        if not isinstance(other, EnchantHeldItemExpression):
            return False
        return (
            self.enchantment_name == other.enchantment_name
            and self.level == other.level
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.enchantment_name} level={self.level}>'


def enchant_held_item(
    enchantment: ALL_ENCHANTMENTS | Enchantment,
    level: int | None = None,
) -> None:
    if isinstance(enchantment, Enchantment):
        name = enchantment.name
        if level is None:
            level = enchantment.level
    else:
        name = enchantment
    if level is None:
        level = 1
    EnchantHeldItemExpression(enchantment_name=name, level=level).write()
