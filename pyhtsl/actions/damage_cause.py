from typing import Self, final

from ..expression.condition.condition import Condition
from ..types import ALL_DAMAGE_CAUSES

__all__ = ('DamageCause',)


@final
class DamageCause(Condition):
    damage_cause: str

    def __init__(
        self,
        damage_cause: ALL_DAMAGE_CAUSES,
    ) -> None:
        self.damage_cause = damage_cause

    def into_htsl_raw(self) -> str:
        return f'damageCause {self.inline_quoted(self.damage_cause)}'

    def cloned_raw(self) -> Self:
        return self.__class__(damage_cause=self.damage_cause)

    def equals_raw(self, other: object) -> bool:
        if not isinstance(other, DamageCause):
            return False
        return self.damage_cause == other.damage_cause

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.damage_cause} inverted={self.inverted}>'
