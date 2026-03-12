import re
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('HouseCookies',)


@final
class HouseCookiesPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%house.cookies%')),
    pattern_factory=lambda _: HouseCookies,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%house.cookies%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(0)

    def cloned_raw(self) -> Self:
        return self.__class__()


HouseCookies = HouseCookiesPlaceholder()
