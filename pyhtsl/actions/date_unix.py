import re
import time
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'DateUnixMSPlaceholder',
    'DateUnixMS',
    'DateUnixPlaceholder',
    'DateUnix',
)


@final
class DateUnixPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%date.unix%')),
    pattern_factory=lambda _: DateUnix,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%date.unix%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(int(time.time()))

    def cloned_raw(self) -> Self:
        return self.__class__()


DateUnix = DateUnixPlaceholder()


@final
class DateUnixMSPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%date.unix.ms%')),
    pattern_factory=lambda _: DateUnixMS,
):
    def __init__(self) -> None:
        super().__init__(
            as_string='%date.unix.ms%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(int(time.time() * 1000))

    def cloned_raw(self) -> Self:
        return self.__class__()


DateUnixMS = DateUnixMSPlaceholder()
