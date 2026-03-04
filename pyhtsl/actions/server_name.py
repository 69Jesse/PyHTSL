from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('ServerName',)


ServerName = PlaceholderCheckable(
    assignment_right_side='%server.name%',
    comparison_left_side='placeholder "%server.name%"',
    comparison_right_side='%server.name%',
    in_string='%server.name%',
    constant_internal_type=InternalType.STRING,
    default_backend_value='',
)
