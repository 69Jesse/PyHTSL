import re
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'HousePlayersPlaceholder',
    'HousePlayers',
)


@final
class HousePlayersPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.players%')),
    pattern_factory=lambda _: HousePlayers,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%house.players%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


HousePlayers = HousePlayersPlaceholder()
