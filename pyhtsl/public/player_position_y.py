from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerPositionY',
)


PlayerPositionY = PlaceholderCheckable(
    assignment_right_side='%player.pos.y%',
    comparison_left_side='placeholder "%player.pos.y%"',
    comparison_right_side='%player.pos.y%',
    in_string='%player.pos.y%',
)
