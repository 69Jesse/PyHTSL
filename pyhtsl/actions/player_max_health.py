import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderEditable

__all__ = ('PlayerMaxHealth',)


class PlayerMaxHealthPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.maxhealth%')),
    pattern_factory=lambda _: PlayerMaxHealth,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_left_side='maxHealth',
            assignment_right_side='%player.maxhealth%',
            comparison_left_side='placeholder "%player.maxhealth%"',
            comparison_right_side='%player.maxhealth%',
            in_string='%player.maxhealth%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)


PlayerMaxHealth = PlayerMaxHealthPlaceholder()
