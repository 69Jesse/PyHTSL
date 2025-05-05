from ..placeholders import PlaceholderCheckable


__all__ = (
    'HouseVisitingRules',
)


HouseVisitingRules = PlaceholderCheckable(
    assignment_right_side='%house.visitingrules%',
    comparison_left_side='placeholder "%house.visitingrules%"',
    comparison_right_side='%house.visitingrules%',
    in_string='%house.visitingrules%',
)
