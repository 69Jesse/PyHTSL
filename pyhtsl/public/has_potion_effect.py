from ..condition import TinyCondition
from ..types import POTION_EFFECTS

from typing import final


__all__ = (
    'HasPotionEffect',
)


@final
class HasPotionEffect(TinyCondition):
    effect: str
    def __init__(
        self,
        effect: POTION_EFFECTS,
    ) -> None:
        self.effect = effect

    def __str__(self) -> str:
        return f'hasPotion "{self.effect}"'
