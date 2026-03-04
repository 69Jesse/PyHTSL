import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderEditable

__all__ = ('PlayerHealth',)


PlayerHealth = PlaceholderEditable(
    assignment_left_side='changeHealth',
    assignment_right_side='%player.health%',
    comparison_left_side='placeholder "%player.health%"',
    comparison_right_side='%player.health%',
    in_string='%player.health%',
    constant_internal_type=InternalType.DOUBLE,
    default_backend_value=np.float64(0),
)
