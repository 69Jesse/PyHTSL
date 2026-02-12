from typing import final

from ..condition.base_condition import BaseCondition
from ..types import ALL_POTION_EFFECTS

__all__ = ('HasPotionEffect',)


@final
class HasPotionEffect(BaseCondition):
    effect: str

    def __init__(
        self,
        effect: ALL_POTION_EFFECTS,
    ) -> None:
        self.effect = effect

    def into_htsl_raw(self) -> str:
        return f'hasPotion "{self.effect}"'
