import re
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'PlayerBlockXPlaceholder',
    'PlayerBlockX',
)


@final
class PlayerBlockXPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.block.x%')),
    pattern_factory=lambda _: PlayerBlockX,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.block.x%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


PlayerBlockX = PlayerBlockXPlaceholder()
