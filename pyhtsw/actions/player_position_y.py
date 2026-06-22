import re
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerPositionYPlaceholder',
    'PlayerPositionY',
)


@final
class PlayerPositionYPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.y%')),
    pattern_factory=lambda _: PlayerPositionY,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.pos.y%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


PlayerPositionY = PlayerPositionYPlaceholder()
