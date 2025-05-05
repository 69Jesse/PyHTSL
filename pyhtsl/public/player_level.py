from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerLevel',
)


PlayerLevel = PlaceholderCheckable(
    assignment_right_side='%player.level%',
    comparison_left_side='placeholder "%player.level%"',
    comparison_right_side='%player.level%',
    in_string='%player.level%',
)
