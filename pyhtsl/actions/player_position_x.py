import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerPositionX',)


class PlayerPositionXPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.x%')),
    pattern_factory=lambda _: PlayerPositionX,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.pos.x%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionX = PlayerPositionXPlaceholder()
