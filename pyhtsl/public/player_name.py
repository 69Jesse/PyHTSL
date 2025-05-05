from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerName',
)


PlayerName = PlaceholderCheckable(
    assignment_right_side='%player.name%',
    comparison_left_side='placeholder "%player.name%"',
    comparison_right_side='%player.name%',
    in_string='%player.name%',
)
