import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderEditable

__all__ = ('PlayerHunger',)


class PlayerHungerPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.hunger%')),
    pattern_factory=lambda _: PlayerHunger,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_left_side='hunger',
            assignment_right_side='%player.hunger%',
            comparison_left_side='placeholder "%player.hunger%"',
            comparison_right_side='%player.hunger%',
            in_string='%player.hunger%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


PlayerHunger = PlayerHungerPlaceholder()
