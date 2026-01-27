from ..placeholders import PlaceholderCheckable


__all__ = ('PlayerGamemode',)


PlayerGamemode = PlaceholderCheckable(
    assignment_right_side='%player.gamemode%',
    comparison_left_side='placeholder "%player.gamemode%"',
    comparison_right_side='%player.gamemode%',
    in_string='%player.gamemode%',
)
