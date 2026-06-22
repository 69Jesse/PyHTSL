from typing import Self, final

from ..expression.condition.condition import Condition
from ..types import ALL_POTION_EFFECTS

__all__ = ('HasPotionEffect',)


@final
class HasPotionEffect(Condition):
    effect: ALL_POTION_EFFECTS

    def __init__(
        self,
        effect: ALL_POTION_EFFECTS,
    ) -> None:
        self.effect = effect

    def into_htsl_raw(self) -> str:
        return f'hasPotion {self.inline_quoted(self.effect)}'

    def cloned_raw(self) -> Self:
        return self.__class__(
            effect=self.effect,
        )

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, HasPotionEffect):
            return False
        return self.effect == other.effect

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.effect} inverted={self.inverted}>'
