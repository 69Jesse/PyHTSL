import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('HouseGuests',)


HouseGuests = PlaceholderCheckable(
    assignment_right_side='%house.guests%',
    comparison_left_side='placeholder "%house.guests%"',
    comparison_right_side='%house.guests%',
    in_string='%house.guests%',
    constant_internal_type=InternalType.LONG,
    backend_value=np.int64(0),
)
