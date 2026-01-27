from ..placeholders import PlaceholderCheckable


__all__ = ('TeamColor',)


TeamColor = PlaceholderCheckable(
    assignment_right_side='%player.team.color%',
    comparison_left_side='placeholder "%player.team.color%"',
    comparison_right_side='%player.team.color%',
    in_string='%player.team.color%',
)
