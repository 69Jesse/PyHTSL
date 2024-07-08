from ..condition import TinyCondition
from ..types import ALL_DAMAGE_CAUSES

from typing import final


__all__ = (
    'DamageCause',
)


@final
class DamageCause(TinyCondition):
    damage_cause: str
    def __init__(
        self,
        damage_cause: ALL_DAMAGE_CAUSES,
    ) -> None:
        self.damage_cause = damage_cause

    def __str__(self) -> str:
        return f'damageCause "{self.damage_cause}"'
