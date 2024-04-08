from ..condition import TinyCondition

from typing import final, Literal


__all__ = (
    'HasPotionEffect',
)


@final
class HasPotionEffect(TinyCondition):
    effect: str
    def __init__(
        self,
        effect: Literal[
            'speed',
            'slowness',
            'haste',
            'mining_fatigue',
            'strength',
            'instant_health',
            'instant_damage',
            'jump_boost',
            'nausea',
            'regeneration',
            'resistance',
            'fire_resistance',
            'water_breathing',
            'invisibility',
            'blindness',
            'night_vision',
            'hunger',
            'weakness',
            'poison',
            'wither',
            'health_boost',
            'absorption',
        ],
    ) -> None:
        self.effect = effect

    def __str__(self) -> str:
        return f'hasPotion "{self.effect}"'
