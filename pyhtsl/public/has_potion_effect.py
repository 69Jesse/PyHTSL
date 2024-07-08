from ..condition import TinyCondition
from ..types import ALL_POTION_EFFECTS

from typing import final


__all__ = (
    'HasPotionEffect',
)


@final
class HasPotionEffect(TinyCondition):
    effect: str
    def __init__(
        self,
        effect: ALL_POTION_EFFECTS,
    ) -> None:
        self.effect = effect

    def __str__(self) -> str:
        return f'hasPotion "{self.effect}"'
