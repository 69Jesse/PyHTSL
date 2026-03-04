from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('TeamName',)


TeamName = PlaceholderCheckable(
    assignment_right_side='%player.team.name%',
    comparison_left_side='placeholder "%player.team.name%"',
    comparison_right_side='%player.team.name%',
    in_string='%player.team.name%',
    constant_internal_type=InternalType.STRING,
    backend_value='',
)
