import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerBlockZ',)


class PlayerBlockZPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.z%')),
    pattern_factory=lambda _: PlayerBlockZ,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.block.z%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


PlayerBlockZ = PlayerBlockZPlaceholder()
