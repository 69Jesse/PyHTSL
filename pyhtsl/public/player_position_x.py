from ..placeholders import PlaceholderCheckable


__all__ = ('PlayerPositionX',)


PlayerPositionX = PlaceholderCheckable(
    assignment_right_side='%player.pos.x%',
    comparison_left_side='placeholder "%player.pos.x%"',
    comparison_right_side='%player.pos.x%',
    in_string='%player.pos.x%',
)
