import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerPositionYaw',)


class PlayerPositionYawPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.yaw%')),
    pattern_factory=lambda _: PlayerPositionYaw,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.pos.yaw%',
            comparison_left_side='placeholder "%player.pos.yaw%"',
            comparison_right_side='%player.pos.yaw%',
            in_string='%player.pos.yaw%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionYaw = PlayerPositionYawPlaceholder()
