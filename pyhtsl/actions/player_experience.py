import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('PlayerExperience',)


class PlayerExperiencePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.experience%')),
    pattern_factory=lambda _: PlayerExperience,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%player.experience%',
            comparison_left_side='placeholder "%player.experience%"',
            comparison_right_side='%player.experience%',
            in_string='%player.experience%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


PlayerExperience = PlayerExperiencePlaceholder()
