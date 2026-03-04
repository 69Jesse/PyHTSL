import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerPositionZ',)


PlayerPositionZ = PlaceholderCheckable(
    assignment_right_side='%player.pos.z%',
    comparison_left_side='placeholder "%player.pos.z%"',
    comparison_right_side='%player.pos.z%',
    in_string='%player.pos.z%',
    constant_internal_type=InternalType.DOUBLE,
    backend_value=np.float64(0),
)
