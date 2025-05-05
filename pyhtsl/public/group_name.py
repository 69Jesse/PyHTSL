from ..placeholders import PlaceholderCheckable


__all__ = (
    'GroupName',
)


GroupName = PlaceholderCheckable(
    assignment_right_side='%player.group.name%',
    comparison_left_side='placeholder "%player.group.name%"',
    comparison_right_side='%player.group.name%',
    in_string='%player.group.name%',
)
