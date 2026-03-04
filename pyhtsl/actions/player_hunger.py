import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderEditable

__all__ = ('PlayerHunger',)


PlayerHunger = PlaceholderEditable(
    assignment_left_side='hunger',
    assignment_right_side='%player.hunger%',
    comparison_left_side='placeholder "%player.hunger%"',
    comparison_right_side='%player.hunger%',
    in_string='%player.hunger%',
    constant_internal_type=InternalType.LONG,
    default_backend_value=np.int64(0),
)
