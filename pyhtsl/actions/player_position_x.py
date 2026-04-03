import re
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerPositionXPlaceholder',
    'PlayerPositionX',
)


@final
class PlayerPositionXPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.pos.x%')),
    pattern_factory=lambda _: PlayerPositionX,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.pos.x%',
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


PlayerPositionX = PlayerPositionXPlaceholder()
