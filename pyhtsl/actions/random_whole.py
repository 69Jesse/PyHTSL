import random
import re

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('RandomWhole',)


def _random_whole_factory(match: re.Match[str]) -> 'RandomWholePlaceholder':
    return RandomWholePlaceholder(int(match.group(1)), int(match.group(2)))


class RandomWholePlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(r'%random\.whole/(-?\d+) (-?\d+)%'),
    pattern_factory=_random_whole_factory,
):
    lower_bound: int
    exclusive_upper_bound: int

    def __init__(self, lower_bound: int, exclusive_upper_bound: int) -> None:
        self.lower_bound = lower_bound
        self.exclusive_upper_bound = exclusive_upper_bound
        if self.exclusive_upper_bound <= self.lower_bound:
            raise ValueError('exclusive_upper_bound must be greater than lower_bound')
        key = f'%random.whole/{lower_bound} {exclusive_upper_bound}%'
        super().__init__(
            as_string=key,
            constant_internal_type=InternalType.LONG,
        )

    def get_backend_value(self) -> BackendType:
        return np.int64(random.randint(self.lower_bound, self.exclusive_upper_bound - 1))


def RandomWhole(
    lower_bound: int,
    exclusive_upper_bound: int,
) -> RandomWholePlaceholder:
    return RandomWholePlaceholder(lower_bound, exclusive_upper_bound)
