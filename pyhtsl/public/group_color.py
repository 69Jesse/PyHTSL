from ..placeholders import PlaceholderCheckable


__all__ = (
    'GroupColor',
)


GroupColor = PlaceholderCheckable(
    assignment_right_side='%player.group.color%',
    comparison_left_side='placeholder "%player.group.color%"',
    comparison_right_side='%player.group.color%',
    in_string='%player.group.color%',
)
