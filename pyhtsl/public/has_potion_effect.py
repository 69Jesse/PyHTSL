from ..condition.base_condition import BaseCondition
from ..types import ALL_POTION_EFFECTS

from typing import final


__all__ = (
    'HasPotionEffect',
)


@final
class HasPotionEffect(BaseCondition):
    effect: str
    def __init__(
        self,
        effect: ALL_POTION_EFFECTS,
    ) -> None:
        self.effect = effect

    def create_line(self) -> str:
        return f'hasPotion "{self.effect}"'
