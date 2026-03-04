import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerBlockX',)


PlayerBlockX = PlaceholderCheckable(
    assignment_right_side='%player.block.x%',
    comparison_left_side='placeholder "%player.block.x%"',
    comparison_right_side='%player.block.x%',
    in_string='%player.block.x%',
    constant_internal_type=InternalType.LONG,
    backend_value=np.int64(0),
)
