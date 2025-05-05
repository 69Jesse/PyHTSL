from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerLocationY',
)


PlayerLocationY = PlaceholderCheckable(
    assignment_right_side='%player.location.y%',
    comparison_left_side='placeholder "%player.location.y%"',
    comparison_right_side='%player.location.y%',
    in_string='%player.location.y%',
)
