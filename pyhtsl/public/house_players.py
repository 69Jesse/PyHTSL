from ..placeholders import PlaceholderCheckable


__all__ = (
    'HousePlayers',
)


HousePlayers = PlaceholderCheckable(
    assignment_right_side='%house.players%',
    comparison_left_side='placeholder "%house.players%"',
    comparison_right_side='%house.players%',
    in_string='%house.players%',
)
