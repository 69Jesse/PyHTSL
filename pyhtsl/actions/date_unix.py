import re
import time

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'DateUnix',
    'DateUnixMS',
)


class DateUnixPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%date.unix%')),
    pattern_factory=lambda _: DateUnix,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%date.unix%',
            comparison_left_side='placeholder "%date.unix%"',
            comparison_right_side='%date.unix%',
            in_string='%date.unix%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(int(time.time()))


DateUnix = DateUnixPlaceholder()


class DateUnixMSPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(re.escape('%date.unix.ms%')),
    pattern_factory=lambda _: DateUnixMS,
):
    def __init__(self) -> None:
        super().__init__(
            assignment_right_side='%date.unix.ms%',
            comparison_left_side='placeholder "%date.unix.ms%"',
            comparison_right_side='%date.unix.ms%',
            in_string='%date.unix.ms%',
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(int(time.time() * 1000))


DateUnixMS = DateUnixMSPlaceholder()
