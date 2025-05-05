from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerLocationZ',
)


PlayerLocationZ = PlaceholderCheckable(
    assignment_right_side='%player.location.z%',
    comparison_left_side='placeholder "%player.location.z%"',
    comparison_right_side='%player.location.z%',
    in_string='%player.location.z%',
)
