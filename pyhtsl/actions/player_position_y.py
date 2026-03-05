import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerPositionY',)


class PlayerPositionYPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.y%')),
    pattern_factory=lambda _: PlayerPositionY,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.pos.y%',
            comparison_left_side='placeholder "%player.pos.y%"',
            comparison_right_side='%player.pos.y%',
            in_string='%player.pos.y%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionY = PlayerPositionYPlaceholder()
