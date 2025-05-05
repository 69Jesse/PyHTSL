from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerLocationPitch',
)


PlayerLocationPitch = PlaceholderCheckable(
    assignment_right_side='%player.location.pitch%',
    comparison_left_side='placeholder "%player.location.pitch%"',
    comparison_right_side='%player.location.pitch%',
    in_string='%player.location.pitch%',
)
