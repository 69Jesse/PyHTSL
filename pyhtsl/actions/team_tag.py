from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('TeamTag',)


TeamTag = PlaceholderCheckable(
    assignment_right_side='%player.team.tag%',
    comparison_left_side='placeholder "%player.team.tag%"',
    comparison_right_side='%player.team.tag%',
    in_string='%player.team.tag%',
    constant_internal_type=InternalType.STRING,
    backend_value='',
)
