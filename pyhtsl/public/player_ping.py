from ..placeholders import PlaceholderCheckable


__all__ = ('PlayerPing',)


PlayerPing = PlaceholderCheckable(
    assignment_right_side='%player.ping%',
    comparison_left_side='placeholder "%player.ping%"',
    comparison_right_side='%player.ping%',
    in_string='%player.ping%',
)
