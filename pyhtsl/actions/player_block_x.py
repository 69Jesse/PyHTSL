import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerBlockX',)


class PlayerBlockXPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.x%')),
    pattern_factory=lambda _: PlayerBlockX,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.block.x%',
            comparison_left_side='placeholder "%player.block.x%"',
            comparison_right_side='%player.block.x%',
            in_string='%player.block.x%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


PlayerBlockX = PlayerBlockXPlaceholder()
