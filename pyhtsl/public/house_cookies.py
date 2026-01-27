from ..placeholders import PlaceholderCheckable


__all__ = ('HouseCookies',)


HouseCookies = PlaceholderCheckable(
    assignment_right_side='%house.cookies%',
    comparison_left_side='placeholder "%house.cookies%"',
    comparison_right_side='%house.cookies%',
    in_string='%house.cookies%',
)
