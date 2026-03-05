import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderEditable

__all__ = ('PlayerHealth',)


class PlayerHealthPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.health%')),
    pattern_factory=lambda _: PlayerHealth,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_left_side='changeHealth',
            assignment_right_side='%player.health%',
            comparison_left_side='placeholder "%player.health%"',
            comparison_right_side='%player.health%',
            in_string='%player.health%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerHealth = PlayerHealthPlaceholder()
