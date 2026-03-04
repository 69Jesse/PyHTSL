from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('GroupTag',)


GroupTag = PlaceholderCheckable(
    assignment_right_side='%player.group.tag%',
    comparison_left_side='placeholder "%player.group.tag%"',
    comparison_right_side='%player.group.tag%',
    in_string='%player.group.tag%',
    constant_internal_type=InternalType.STRING,
    default_backend_value='',
)
