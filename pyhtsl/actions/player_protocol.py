import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerProtocol',)


class PlayerProtocolPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.protocol%')),
    pattern_factory=lambda _: PlayerProtocol,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.protocol%',
            comparison_left_side='placeholder "%player.protocol%"',
            comparison_right_side='%player.protocol%',
            in_string='%player.protocol%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


PlayerProtocol = PlayerProtocolPlaceholder()
