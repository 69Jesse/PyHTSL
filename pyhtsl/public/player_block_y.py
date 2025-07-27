from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerBlockY',
)


PlayerBlockY = PlaceholderCheckable(
    assignment_right_side='%player.block.y%',
    comparison_left_side='placeholder "%player.block.y%"',
    comparison_right_side='%player.block.y%',
    in_string='%player.block.y%',
)
