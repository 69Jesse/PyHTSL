from ..write import write

from typing import Literal


__all__ = (
    'apply_potion_effect',
)


def apply_potion_effect(
    potion: Literal[
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
    duration: int = 60,
    level: int = 1,
    override_existing_effects: bool = False,
) -> None:
    write(f'applyPotion "{potion}" {duration} {level} {str(override_existing_effects).lower()}')
