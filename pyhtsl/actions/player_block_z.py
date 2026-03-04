import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerBlockZ',)


PlayerBlockZ = PlaceholderCheckable(
    assignment_right_side='%player.block.z%',
    comparison_left_side='placeholder "%player.block.z%"',
    comparison_right_side='%player.block.z%',
    in_string='%player.block.z%',
    constant_internal_type=InternalType.LONG,
    backend_value=np.int64(0),
)
