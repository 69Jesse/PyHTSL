from typing import final

from ..condition.base_condition import BaseCondition
from ..types import ALL_DAMAGE_CAUSES

__all__ = ('DamageCause',)


@final
class DamageCause(BaseCondition):
    damage_cause: str

    def __init__(
        self,
        damage_cause: ALL_DAMAGE_CAUSES,
    ) -> None:
        self.damage_cause = damage_cause

    def into_htsl_raw(self) -> str:
        return f'damageCause "{self.damage_cause}"'
