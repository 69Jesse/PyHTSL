import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('HousePlayers',)


class HousePlayersPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.players%')),
    pattern_factory=lambda _: HousePlayers,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%house.players%',
            comparison_left_side='placeholder "%house.players%"',
            comparison_right_side='%house.players%',
            in_string='%house.players%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


HousePlayers = HousePlayersPlaceholder()
