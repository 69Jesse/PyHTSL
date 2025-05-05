from ..placeholders import PlaceholderCheckable


__all__ = (
    'ServerShortName',
)


ServerShortName = PlaceholderCheckable(
    assignment_right_side='%server.shortname%',
    comparison_left_side='placeholder "%server.shortname%"',
    comparison_right_side='%server.shortname%',
    in_string='%server.shortname%',
)
