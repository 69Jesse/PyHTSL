import random
import re
from typing import Self, final

import numpy as np

from ..execute.backend_type import BackendType
from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = (
    'RandomDecimalPlaceholder',
    'RandomDecimal',
)


def _random_decimal_factory(match: re.Match[str]) -> 'RandomDecimalPlaceholder':
    return RandomDecimalPlaceholder(float(match.group(1)), float(match.group(2)))


@final
class RandomDecimalPlaceholder(
    PlaceholderCheckable,
    pattern=re.compile(r'%random\.decimal/([\d.\-]+) ([\d.\-]+)%'),
    pattern_factory=_random_decimal_factory,
):
    lower_bound: float
    exclusive_upper_bound: float

    def __init__(self, lower_bound: float, exclusive_upper_bound: float) -> None:
        self.lower_bound = lower_bound
        self.exclusive_upper_bound = exclusive_upper_bound
        key = f'%random.decimal/{lower_bound} {exclusive_upper_bound}%'
        if self.exclusive_upper_bound <= self.lower_bound:
            raise ValueError('exclusive_upper_bound must be greater than lower_bound')
        super().__init__(
            as_string=key,
            constant_internal_type=InternalType.DOUBLE,
        )

    def get_backend_value(self) -> BackendType:
        return np.float64(random.uniform(self.lower_bound, self.exclusive_upper_bound))

    def cloned_raw(self) -> Self:
        return self.__class__(
            lower_bound=self.lower_bound,
            exclusive_upper_bound=self.exclusive_upper_bound,
        )


def RandomDecimal(
    lower_bound: float,
    exclusive_upper_bound: float,
) -> RandomDecimalPlaceholder:
    return RandomDecimalPlaceholder(lower_bound, exclusive_upper_bound)
