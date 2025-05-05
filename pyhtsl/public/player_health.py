from ..stats import EdgeCaseEditable


__all__ = (
    'PlayerHealth',
)


PlayerHealth = EdgeCaseEditable('health', '%player.health%', 'changeHealth')
