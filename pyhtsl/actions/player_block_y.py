import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerBlockY',)


class PlayerBlockYPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.y%')),
    pattern_factory=lambda _: PlayerBlockY,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.block.y%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


PlayerBlockY = PlayerBlockYPlaceholder()
