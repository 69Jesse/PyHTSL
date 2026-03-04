import numpy as np

from ..internal_type import InternalType
from ..placeholders import PlaceholderCheckable

__all__ = ('RandomWhole',)


def RandomWhole(
    lower_bound: int,
    exclusive_upper_bound: int,
) -> PlaceholderCheckable:
    key = f'%random.whole/{lower_bound} {exclusive_upper_bound}%'
    return PlaceholderCheckable(
        assignment_right_side=f'{key}',
        comparison_left_side=f'placeholder "{key}"',
        comparison_right_side=f'{key}',
        in_string=f'{key}',
        constant_internal_type=InternalType.LONG,
        backend_value=np.int64(0),
    )
