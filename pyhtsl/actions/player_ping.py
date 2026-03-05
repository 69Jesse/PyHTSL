import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerPing',)


class PlayerPingPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.ping%')),
    pattern_factory=lambda _: PlayerPing,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.ping%',
            comparison_left_side='placeholder "%player.ping%"',
            comparison_right_side='%player.ping%',
            in_string='%player.ping%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


PlayerPing = PlayerPingPlaceholder()
