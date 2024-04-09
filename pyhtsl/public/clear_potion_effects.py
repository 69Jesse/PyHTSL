from ..write import write


__all__ = (
    'clear_potion_effects',
)


def clear_potion_effects() -> None:
    write('clearEffects')
