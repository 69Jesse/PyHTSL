import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerPositionPitch',)


class PlayerPositionPitchPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.pitch%')),
    pattern_factory=lambda _: PlayerPositionPitch,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.pos.pitch%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerPositionPitch = PlayerPositionPitchPlaceholder()
