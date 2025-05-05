from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerLocationX',
)


PlayerLocationX = PlaceholderCheckable(
    assignment_right_side='%player.location.x%',
    comparison_left_side='placeholder "%player.location.x%"',
    comparison_right_side='%player.location.x%',
    in_string='%player.location.x%',
)
