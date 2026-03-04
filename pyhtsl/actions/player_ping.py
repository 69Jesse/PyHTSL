import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerPing',)


PlayerPing = PlaceholderCheckable(
    assignment_right_side='%player.ping%',
    comparison_left_side='placeholder "%player.ping%"',
    comparison_right_side='%player.ping%',
    in_string='%player.ping%',
    constant_internal_type=InternalType.LONG,
    default_backend_value=np.int64(0),
)
