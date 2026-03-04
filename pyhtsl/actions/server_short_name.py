from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('ServerShortName',)


ServerShortName = PlaceholderCheckable(
    assignment_right_side='%server.shortname%',
    comparison_left_side='placeholder "%server.shortname%"',
    comparison_right_side='%server.shortname%',
    in_string='%server.shortname%',
    constant_internal_type=InternalType.STRING,
    default_backend_value='',
)
