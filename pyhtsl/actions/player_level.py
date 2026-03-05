import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerLevel',)


class PlayerLevelPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.level%')),
    pattern_factory=lambda _: PlayerLevel,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.level%',
            comparison_left_side='placeholder "%player.level%"',
            comparison_right_side='%player.level%',
            in_string='%player.level%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


PlayerLevel = PlayerLevelPlaceholder()
