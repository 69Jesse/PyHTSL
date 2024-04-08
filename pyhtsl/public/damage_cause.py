from ..condition import TinyCondition

from typing import final, Literal


__all__ = (
    'DamageCause',
)


@final
class DamageCause(TinyCondition):
    damage_cause: str
    def __init__(
        self,
        damage_cause: Literal[
            'entity Attack',
            'projectile',
            'suffocation',
            'fall',
            'lava',
            'fire',
            'fire_tick',
            'drowning',
            'starvation',
            'poison',
            'thorns',
        ],
    ) -> None:
        self.damage_cause = damage_cause

    def __str__(self) -> str:
        return f'damageCause "{self.damage_cause}"'
