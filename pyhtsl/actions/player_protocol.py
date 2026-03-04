import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerProtocol',)


PlayerProtocol = PlaceholderCheckable(
    assignment_right_side='%player.protocol%',
    comparison_left_side='placeholder "%player.protocol%"',
    comparison_right_side='%player.protocol%',
    in_string='%player.protocol%',
    constant_internal_type=InternalType.LONG,
    backend_value=np.int64(0),
)
