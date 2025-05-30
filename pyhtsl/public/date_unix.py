from ..placeholders import PlaceholderCheckable


__all__ = (
    'DateUnix',
    'DateUnixMS',
)


DateUnix = PlaceholderCheckable(
    assignment_right_side='%date.unix%',
    comparison_left_side='placeholder "%date.unix%"',
    comparison_right_side='%date.unix%',
    in_string='%date.unix%',
)


DateUnixMS = PlaceholderCheckable(
    assignment_right_side='%date.unix.ms%',
    comparison_left_side='placeholder "%date.unix.ms%"',
    comparison_right_side='%date.unix.ms%',
    in_string='%date.unix.ms%',
)
