from ..stat import ComparableStat


__all__ = (
    'PlayerHealth',
)


PlayerHealth = ComparableStat('health', '%player.health%', 'changeHealth')
