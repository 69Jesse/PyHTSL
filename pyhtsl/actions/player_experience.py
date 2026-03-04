import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerExperience',)


PlayerExperience = PlaceholderCheckable(
    assignment_right_side='%player.experience%',
    comparison_left_side='placeholder "%player.experience%"',
    comparison_right_side='%player.experience%',
    in_string='%player.experience%',
    constant_internal_type=InternalType.LONG,
    default_backend_value=np.int64(0),
)
