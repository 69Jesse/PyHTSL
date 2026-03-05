import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('HouseGuests',)


class HouseGuestsPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.guests%')),
    pattern_factory=lambda _: HouseGuests,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%house.guests%',
            comparison_left_side='placeholder "%house.guests%"',
            comparison_right_side='%house.guests%',
            in_string='%house.guests%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


HouseGuests = HouseGuestsPlaceholder()
