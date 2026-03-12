import re
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerPositionYaw',)


@final
class PlayerPositionYawPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.yaw%')),
    pattern_factory=lambda _: PlayerPositionYaw,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.pos.yaw%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


PlayerPositionYaw = PlayerPositionYawPlaceholder()
