from ..placeholders import PlaceholderCheckable


__all__ = ('PlayerPositionZ',)


PlayerPositionZ = PlaceholderCheckable(
    assignment_right_side='%player.pos.z%',
    comparison_left_side='placeholder "%player.pos.z%"',
    comparison_right_side='%player.pos.z%',
    in_string='%player.pos.z%',
)
