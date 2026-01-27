from ..placeholders import PlaceholderCheckable


__all__ = ('PlayerPositionPitch',)


PlayerPositionPitch = PlaceholderCheckable(
    assignment_right_side='%player.pos.pitch%',
    comparison_left_side='placeholder "%player.pos.pitch%"',
    comparison_right_side='%player.pos.pitch%',
    in_string='%player.pos.pitch%',
)
