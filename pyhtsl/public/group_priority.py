from ..placeholders import PlaceholderCheckable


__all__ = (
    'GroupPriority',
)


GroupPriority = PlaceholderCheckable(
    assignment_right_side='%player.group.priority%',
    comparison_left_side='placeholder "%player.group.priority%"',
    comparison_right_side='%player.group.priority%',
    in_string='%player.group.priority%',
)
