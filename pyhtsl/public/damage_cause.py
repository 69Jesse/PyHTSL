from ..condition.base_condition import BaseCondition
from ..types import ALL_DAMAGE_CAUSES

from typing import final


__all__ = (
    'DamageCause',
)


@final
class DamageCause(BaseCondition):
    damage_cause: str
    def __init__(
        self,
        damage_cause: ALL_DAMAGE_CAUSES,
    ) -> None:
        self.damage_cause = damage_cause

    def create_line(self) -> str:
        return f'damageCause "{self.damage_cause}"'
