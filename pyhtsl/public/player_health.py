from ..placeholders import PlaceholderEditable


__all__ = (
    'PlayerHealth',
)


PlayerHealth = PlaceholderEditable(
    assignment_left_side='health',
    assignment_right_side='%player.health%',
    comparison_left_side='placeholder "%player.health%"',
    comparison_right_side='%player.health%',
    in_string='%player.health%',
)
