from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerVersion',
)


PlayerVersion = PlaceholderCheckable(
    assignment_right_side='%player.version%',
    comparison_left_side='placeholder "%player.version%"',
    comparison_right_side='%player.version%',
    in_string='%player.version%',
)
