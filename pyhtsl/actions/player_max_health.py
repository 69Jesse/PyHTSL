import re
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderEditable

__all__ = ('PlayerMaxHealth',)


@final
class PlayerMaxHealthPlaceholder(
    PlaceholderEditable,
    pattern=re.compile(re.escape('%player.maxhealth%')),
    pattern_factory=lambda _: PlayerMaxHealth,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_lhs='maxHealth',
            as_string='%player.maxhealth%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


PlayerMaxHealth = PlayerMaxHealthPlaceholder()
