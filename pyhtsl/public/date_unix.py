from ..placeholders import PlaceholderCheckable


__all__ = (
    'DateUnix',
)


DateUnix = PlaceholderCheckable(
    assignment_right_side='%date.unix%',
    comparison_left_side='placeholder "%date.unix%"',
    comparison_right_side='%date.unix%',
    in_string='%date.unix%',
)
