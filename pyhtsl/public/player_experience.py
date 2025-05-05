from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerExperience',
)


PlayerExperience = PlaceholderCheckable(
    assignment_right_side='%player.experience%',
    comparison_left_side='placeholder "%player.experience%"',
    comparison_right_side='%player.experience%',
    in_string='%player.experience%',
)
