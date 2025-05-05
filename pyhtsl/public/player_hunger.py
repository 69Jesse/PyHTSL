from ..placeholders import PlaceholderEditable


__all__ = (
    'PlayerHunger',
)


PlayerHunger = PlaceholderEditable(
    assignment_left_side='hunger',
    assignment_right_side='%player.hunger%',
    comparison_left_side='placeholder "%player.hunger%"',
    comparison_right_side='%player.hunger%',
    in_string='%player.hunger%',
)
