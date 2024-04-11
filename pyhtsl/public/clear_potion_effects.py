from ..writer import WRITER


__all__ = (
    'clear_potion_effects',
)


def clear_potion_effects() -> None:
    WRITER.write('clearEffects')
