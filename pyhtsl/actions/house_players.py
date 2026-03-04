import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('HousePlayers',)


HousePlayers = PlaceholderCheckable(
    assignment_right_side='%house.players%',
    comparison_left_side='placeholder "%house.players%"',
    comparison_right_side='%house.players%',
    in_string='%house.players%',
    constant_internal_type=InternalType.LONG,
    backend_value=np.int64(0),
)
