import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('GroupPriority',)


class GroupPriorityPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%player.group.priority%')),
    pattern_factory=lambda _: GroupPriority,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%player.group.priority%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)


GroupPriority = GroupPriorityPlaceholder()
