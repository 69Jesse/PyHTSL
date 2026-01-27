from ..placeholders import PlaceholderCheckable


__all__ = ('GroupTag',)


GroupTag = PlaceholderCheckable(
    assignment_right_side='%player.group.tag%',
    comparison_left_side='placeholder "%player.group.tag%"',
    comparison_right_side='%player.group.tag%',
    in_string='%player.group.tag%',
)
